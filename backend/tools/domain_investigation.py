"""Domain investigation - combines WHOIS + DNS + basic reputation checks."""
import requests
from backend.tools import whois_lookup, dns_enum
from backend.config import get_key


def _virustotal(domain: str) -> dict:
    key = get_key("virustotal")
    if not key:
        return {"available": False, "reason": "VirusTotal API key not configured."}
    url = f"https://www.virustotal.com/api/v3/domains/{domain}"
    try:
        r = requests.get(url, headers={"x-apikey": key}, timeout=10)
        if r.status_code == 401:
            return {"available": False, "reason": "Invalid VirusTotal key."}
        r.raise_for_status()
        data = r.json().get("data", {}).get("attributes", {})
        stats = data.get("last_analysis_stats", {})
        return {
            "available": True,
            "reputation": data.get("reputation"),
            "categories": data.get("categories", {}),
            "harmless": stats.get("harmless", 0),
            "malicious": stats.get("malicious", 0),
            "suspicious": stats.get("suspicious", 0),
        }
    except requests.RequestException as e:
        return {"available": False, "reason": str(e)}


def run(target: str) -> dict:
    target = (target or "").strip().lower()
    if not target:
        return {"error": "Domain required."}
    target = target.replace("http://", "").replace("https://", "").split("/")[0]

    whois_result = whois_lookup.run(target)
    dns_result = dns_enum.run(target)
    reputation = _virustotal(target)

    return {
        "target": target,
        "whois": whois_result.get("whois", {"error": whois_result.get("error")}),
        "dns": dns_result.get("records", {"error": dns_result.get("error")}),
        "reputation": reputation,
        "summary": f"Combined WHOIS + DNS + reputation for {target}"
    }
