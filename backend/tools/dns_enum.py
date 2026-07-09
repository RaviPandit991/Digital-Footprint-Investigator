"""DNS enumeration - records, zone transfer, DNSSEC, reverse lookups."""
import socket
import dns.resolver
import dns.query
import dns.zone
import dns.exception
from concurrent.futures import ThreadPoolExecutor

STANDARD_RECORDS = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]
EXTENDED_RECORDS = STANDARD_RECORDS + ["CAA", "SRV", "PTR", "DNSKEY", "DS"]

# Common subdomain prefixes for SPF/DMARC lookup
POLICY_RECORDS = ["_dmarc", "_domainkey", "_spf"]


def _reverse_dns(ip: str) -> str:
    try:
        return socket.gethostbyaddr(ip)[0]
    except (socket.herror, socket.gaierror):
        return ""


def _try_axfr(domain: str, nameservers: list) -> dict:
    """Attempt AXFR zone transfer from each nameserver."""
    result = {"attempted": True, "vulnerable": False, "servers_tried": [], "records": []}
    for ns in nameservers:
        ns_host = ns.rstrip(".")
        try:
            ns_ip = socket.gethostbyname(ns_host)
            zone = dns.zone.from_xfr(dns.query.xfr(ns_ip, domain, timeout=5))
            records = []
            for name, node in zone.nodes.items():
                for rdataset in node.rdatasets:
                    records.append(f"{name} {rdataset}")
            result["vulnerable"] = True
            result["servers_tried"].append({"ns": ns_host, "success": True, "record_count": len(records)})
            result["records"] = records[:100]
            return result
        except Exception as e:
            result["servers_tried"].append({"ns": ns_host, "success": False, "reason": str(e)[:80]})
    return result


def _check_dnssec(domain: str) -> dict:
    resolver = dns.resolver.Resolver()
    resolver.timeout = 3
    try:
        answer = resolver.resolve(domain, "DNSKEY")
        return {"enabled": True, "key_count": len(answer)}
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        return {"enabled": False}
    except dns.exception.DNSException:
        return {"enabled": None, "reason": "Query failed"}


def _query_policy_records(domain: str) -> dict:
    resolver = dns.resolver.Resolver()
    resolver.timeout = 3
    policies = {}
    try:
        r = resolver.resolve(f"_dmarc.{domain}", "TXT")
        policies["dmarc"] = [str(rd).strip('"') for rd in r]
    except dns.exception.DNSException:
        policies["dmarc"] = []
    # SPF is normally in root TXT records
    try:
        r = resolver.resolve(domain, "TXT")
        spf = [str(rd).strip('"') for rd in r if "v=spf1" in str(rd).lower()]
        policies["spf"] = spf
    except dns.exception.DNSException:
        policies["spf"] = []
    return policies


def run(target: str, mode: str = "basic", zone_transfer: bool = False,
        reverse_lookup: bool = False, check_policies: bool = False) -> dict:
    """DNS enumeration.

    mode: 'basic' (7 record types) or 'advanced' (12 record types + extras)
    zone_transfer: attempt AXFR from each NS server
    reverse_lookup: reverse-DNS all A records
    check_policies: also fetch SPF/DMARC records
    """
    target = (target or "").strip().lower()
    if not target:
        return {"error": "Domain required."}
    target = target.replace("http://", "").replace("https://", "").split("/")[0]

    record_types = EXTENDED_RECORDS if mode == "advanced" else STANDARD_RECORDS
    resolver = dns.resolver.Resolver()
    resolver.timeout = 3
    resolver.lifetime = 5

    results = {}
    for rt in record_types:
        try:
            ans = resolver.resolve(target, rt)
            results[rt] = [str(r) for r in ans]
        except dns.resolver.NoAnswer:
            results[rt] = []
        except dns.resolver.NXDOMAIN:
            return {"error": f"Domain does not exist: {target}"}
        except dns.exception.DNSException as e:
            results[rt] = [f"Error: {str(e)[:60]}"]

    extras = {}

    # Reverse DNS for A records
    if reverse_lookup and results.get("A"):
        ips = [ip for ip in results["A"] if not ip.startswith("Error")]
        with ThreadPoolExecutor(max_workers=10) as ex:
            ptrs = list(ex.map(_reverse_dns, ips))
        extras["reverse_dns"] = {ip: ptr for ip, ptr in zip(ips, ptrs) if ptr}

    # Zone transfer attempt
    if zone_transfer and results.get("NS"):
        extras["zone_transfer"] = _try_axfr(target, results["NS"])

    # DNSSEC + policies (advanced mode gets them automatically)
    if mode == "advanced":
        extras["dnssec"] = _check_dnssec(target)
    if check_policies or mode == "advanced":
        extras["email_policies"] = _query_policy_records(target)

    total = sum(len(v) for v in results.values() if v and not str(v[0]).startswith("Error"))
    return {
        "target": target,
        "mode": mode,
        "records": results,
        "extras": extras,
        "summary": f"Retrieved {total} record(s) across {len(record_types)} types."
                   + (" | AXFR attempted" if zone_transfer else "")
                   + (" | DNSSEC checked" if mode == "advanced" else "")
    }
