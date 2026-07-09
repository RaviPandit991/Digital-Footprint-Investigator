"""WHOIS lookup."""
import whois


def _serialize(value):
    if isinstance(value, list):
        return [_serialize(v) for v in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value) if value is not None else None


def run(target: str) -> dict:
    target = (target or "").strip().lower()
    if not target:
        return {"error": "Domain required."}
    target = target.replace("http://", "").replace("https://", "").split("/")[0]

    try:
        w = whois.whois(target)
    except Exception as e:
        return {"error": f"WHOIS lookup failed: {e}"}

    fields = [
        "domain_name", "registrar", "creation_date", "expiration_date",
        "updated_date", "name_servers", "status", "emails", "dnssec",
        "org", "country", "state", "city", "address", "zipcode",
        "registrant_name", "admin_email", "tech_email"
    ]

    data = {}
    for f in fields:
        val = w.get(f) if isinstance(w, dict) else getattr(w, f, None)
        if val:
            data[f] = _serialize(val)

    if not data:
        return {"error": "No WHOIS data available (domain may not exist or registry restricts data)."}

    return {
        "target": target,
        "whois": data,
        "summary": f"Registrar: {data.get('registrar', 'N/A')} | Created: {data.get('creation_date', 'N/A')}"
    }
