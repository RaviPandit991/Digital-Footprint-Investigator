"""Entity extraction from tool results + next-tool suggestion engine."""
import re

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
DOMAIN_RE = re.compile(r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b", re.I)


def extract_entities(tool_id: str, target: str, result: dict) -> list:
    """Extract structured entities from a tool's result.

    Returns list of (entity_type, value) tuples.
    Entity types: email, ip, domain, subdomain, username, phone, url,
                  coordinate, port, tech, hash, cve
    """
    if not result:
        return []
    entities = []

    # Every tool contributes its target as an entity
    if target:
        etype = _classify_target(tool_id, target)
        if etype:
            entities.append((etype, target))

    # Tool-specific extractors
    extractor = _EXTRACTORS.get(tool_id)
    if extractor:
        entities.extend(extractor(result))

    # Dedupe (preserve order)
    seen = set()
    unique = []
    for e in entities:
        key = (e[0], e[1].lower() if isinstance(e[1], str) else e[1])
        if key not in seen:
            seen.add(key)
            unique.append(e)
    return unique


def _classify_target(tool_id: str, target: str) -> str:
    """Infer what kind of entity the tool target is."""
    if "@" in target:
        return "email"
    if IPV4_RE.fullmatch(target.strip()):
        return "ip"
    if target.startswith("+") and any(c.isdigit() for c in target):
        return "phone"
    if tool_id == "username-lookup":
        return "username"
    if tool_id in ("port-scan", "banner-grab", "ssl-scan", "ip-investigation"):
        # host may be IP or domain
        cleaned = target.split(":")[0]
        return "ip" if IPV4_RE.fullmatch(cleaned) else "domain"
    if target.startswith(("http://", "https://")):
        return "url"
    if "." in target and not " " in target:
        return "domain"
    return None


# ============ TOOL-SPECIFIC EXTRACTORS ============

def _extract_port_scan(r):
    ents = []
    if r.get("ip"):
        ents.append(("ip", r["ip"]))
    for p in r.get("open_ports", []):
        ents.append(("port", f"{r.get('ip', '?')}:{p['port']}"))
    return ents


def _extract_dns_enum(r):
    ents = []
    records = r.get("records", {})
    for ip in records.get("A", []) + records.get("AAAA", []):
        if not ip.startswith("Error"):
            ents.append(("ip", ip))
    for mx in records.get("MX", []):
        # "10 mail.example.com."
        parts = mx.split()
        if len(parts) >= 2:
            ents.append(("domain", parts[-1].rstrip(".")))
    for cname in records.get("CNAME", []):
        ents.append(("domain", cname.rstrip(".")))
    for txt in records.get("TXT", []):
        for match in EMAIL_RE.findall(txt):
            ents.append(("email", match))
    # SPF/DMARC extracted emails
    policies = r.get("extras", {}).get("email_policies", {})
    for records_list in policies.values():
        for policy_str in records_list:
            for match in EMAIL_RE.findall(policy_str):
                ents.append(("email", match))
    return ents


def _extract_subdomain(r):
    return [("subdomain", s) for s in r.get("subdomains", [])[:100]]


def _extract_whois(r):
    ents = []
    w = r.get("whois", {})
    for field in ("registrant_email", "admin_email", "tech_email", "emails"):
        val = w.get(field)
        if val:
            if isinstance(val, list):
                for e in val:
                    ents.append(("email", str(e)))
            else:
                for match in EMAIL_RE.findall(str(val)):
                    ents.append(("email", match))
    for field in ("name_servers",):
        val = w.get(field)
        if val:
            if isinstance(val, list):
                for ns in val:
                    ents.append(("domain", str(ns).lower().rstrip(".")))
    return ents


def _extract_dir_brute(r):
    return [("url", f["url"]) for f in r.get("found", [])[:20]]


def _extract_crawler(r):
    ents = []
    for e in r.get("emails") or []:
        ents.append(("email", e))
    for p in r.get("phones") or []:
        ents.append(("phone", p))
    for s in r.get("social_profiles") or []:
        ents.append(("url", f"https://{s}" if not s.startswith("http") else s))
    for h in r.get("external_hosts") or []:
        ents.append(("domain", h))
    return ents


def _extract_ssl_scan(r):
    ents = []
    for san in r.get("san", [])[:20]:
        ents.append(("subdomain" if "." in san else "domain", san))
    return ents


def _extract_username(r):
    ents = []
    for p in r.get("found_on", []):
        ents.append(("url", p.get("url")))
    return ents


def _extract_email(r):
    ents = []
    if r.get("domain"):
        ents.append(("domain", r["domain"]))
    prof = (r.get("gravatar") or {}).get("profile") or {}
    for acc in prof.get("accounts", []):
        if acc.get("username"):
            ents.append(("username", acc["username"]))
        if acc.get("url"):
            ents.append(("url", acc["url"]))
    return ents


def _extract_domain_inv(r):
    ents = []
    dns = r.get("dns", {})
    if isinstance(dns, dict):
        for ip in (dns.get("A") or []) + (dns.get("AAAA") or []):
            if not str(ip).startswith("Error"):
                ents.append(("ip", ip))
    return ents


def _extract_ip_inv(r):
    ents = []
    if r.get("reverse_dns"):
        ents.append(("domain", r["reverse_dns"]))
    shodan = r.get("shodan") or {}
    if shodan.get("available"):
        for h in shodan.get("hostnames") or []:
            ents.append(("domain", h))
        for port in shodan.get("ports") or []:
            ents.append(("port", f"{r.get('ip', '?')}:{port}"))
        for v in shodan.get("vulns") or []:
            ents.append(("cve", v))
    return ents


def _extract_phone(r):
    return []  # target already extracted, nothing new


def _extract_metadata(r):
    ents = []
    m = r.get("metadata") or {}
    gps = m.get("gps_coordinates")
    if gps:
        ents.append(("coordinate", f"{gps.get('lat')},{gps.get('lon')}"))
    return ents


def _extract_website(r):
    ents = []
    for t in r.get("technologies", []):
        ents.append(("tech", t))
    return ents


def _extract_social(r):
    ents = []
    uname = r.get("username_lookup")
    if uname:
        for p in uname.get("found_on", []):
            ents.append(("url", p.get("url")))
    return ents


def _extract_dark_web(r):
    return []  # onion URLs are sensitive, don't auto-add


_EXTRACTORS = {
    "port-scan": _extract_port_scan,
    "dns-enum": _extract_dns_enum,
    "subdomain-enum": _extract_subdomain,
    "whois": _extract_whois,
    "dir-brute": _extract_dir_brute,
    "web-crawler": _extract_crawler,
    "ssl-scan": _extract_ssl_scan,
    "username-lookup": _extract_username,
    "email-investigation": _extract_email,
    "domain-investigation": _extract_domain_inv,
    "ip-investigation": _extract_ip_inv,
    "phone-investigation": _extract_phone,
    "metadata-extraction": _extract_metadata,
    "website-analysis": _extract_website,
    "social-media": _extract_social,
    "dark-web": _extract_dark_web,
}


# ============ SUGGESTION ENGINE ============

# For each entity type, which tools are useful to run next
SUGGESTION_MAP = {
    "email": [
        ("email-investigation", "Email Investigation", "Verify + check breaches"),
        ("breach-check", "Breach Check", "Search HIBP databases"),
        ("username-lookup", "Username Lookup", "Search local part as username"),
    ],
    "ip": [
        ("ip-investigation", "IP Investigation", "Geolocation + ASN + abuse"),
        ("port-scan", "Port Scan", "Discover open services"),
        ("ssl-scan", "SSL Scan", "Check TLS certificate"),
    ],
    "domain": [
        ("domain-investigation", "Domain Investigation", "WHOIS + DNS + reputation"),
        ("subdomain-enum", "Subdomain Enumeration", "Discover subdomains"),
        ("dns-enum", "DNS Enumeration", "Full DNS records"),
        ("ssl-scan", "SSL Scan", "Check TLS certificate"),
        ("website-analysis", "Website Analysis", "Tech stack + trackers"),
    ],
    "subdomain": [
        ("website-analysis", "Website Analysis", "Analyze subdomain"),
        ("ssl-scan", "SSL Scan", "Check subdomain TLS"),
        ("dir-brute", "Directory Bruteforce", "Discover hidden paths"),
    ],
    "username": [
        ("username-lookup", "Username Lookup", "Search 90+ platforms"),
        ("social-media", "Social Media Search", "Aggregated search"),
        ("breach-check", "Breach Check", "Search breach databases"),
    ],
    "phone": [
        ("phone-investigation", "Phone Investigation", "Carrier + region + OSINT"),
    ],
    "url": [
        ("website-analysis", "Website Analysis", "Tech + headers + trackers"),
        ("dir-brute", "Directory Bruteforce", "Hidden paths"),
        ("web-crawler", "Web Crawler", "Follow links + extract data"),
    ],
    "coordinate": [],  # coordinates just show location
    "port": [
        ("banner-grab", "Banner Grab", "Fingerprint service"),
    ],
    "tech": [],
    "cve": [],
    "hash": [],
}


def suggest_next(entities: list, executed_tools: set = None) -> list:
    """Given a list of entity dicts (from db), suggest next tools to run.

    executed_tools: set of (tool_id, target) that were already run — skip these.
    """
    executed = executed_tools or set()
    suggestions = []
    seen = set()

    for e in entities:
        etype = e.get("entity_type") or e.get("type")
        value = e.get("value")
        if not etype or not value:
            continue

        # Special: username extraction from email
        if etype == "email" and "@" in value:
            local = value.split("@")[0]
            if len(local) >= 3 and (local, "username-lookup") not in executed:
                key = ("username-lookup", local)
                if key not in seen:
                    seen.add(key)
                    suggestions.append({
                        "tool_id": "username-lookup",
                        "tool_name": "Username Lookup",
                        "target": local,
                        "reason": f"Email local part '{local}'",
                        "source_entity": {"type": etype, "value": value}
                    })

        for tool_id, tool_name, reason_hint in SUGGESTION_MAP.get(etype, []):
            if (tool_id, value) in executed:
                continue
            key = (tool_id, value)
            if key in seen:
                continue
            seen.add(key)
            suggestions.append({
                "tool_id": tool_id,
                "tool_name": tool_name,
                "target": value,
                "reason": f"{reason_hint} on {etype} '{value}'",
                "source_entity": {"type": etype, "value": value}
            })

    return suggestions[:20]  # cap to top 20
