"""DNS enumeration - query A, AAAA, MX, NS, TXT, CNAME, SOA records."""
import dns.resolver
import dns.exception

RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]


def run(target: str) -> dict:
    target = (target or "").strip().lstrip("http://").lstrip("https://").split("/")[0]
    if not target:
        return {"error": "Domain required."}

    results = {}
    resolver = dns.resolver.Resolver()
    resolver.timeout = 3
    resolver.lifetime = 5

    for record_type in RECORD_TYPES:
        try:
            answers = resolver.resolve(target, record_type)
            results[record_type] = [str(rdata) for rdata in answers]
        except dns.resolver.NoAnswer:
            results[record_type] = []
        except dns.resolver.NXDOMAIN:
            return {"error": f"Domain does not exist: {target}"}
        except dns.exception.DNSException as e:
            results[record_type] = [f"Error: {e}"]

    total = sum(len(v) for v in results.values() if not (v and str(v[0]).startswith("Error")))
    return {
        "target": target,
        "records": results,
        "summary": f"Retrieved {total} DNS record(s) across {len(RECORD_TYPES)} types."
    }
