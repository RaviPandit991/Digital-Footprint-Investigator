"""IP investigation - geolocation, ASN, reverse DNS, abuse, Shodan."""
import socket
import ipaddress
import requests
from backend.config import get_key


def _geolocate(ip: str) -> dict:
    """Uses ip-api.com (no key, 45 req/min)."""
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}?fields=66846719", timeout=8)
        r.raise_for_status()
        data = r.json()
        if data.get("status") != "success":
            return {"error": data.get("message", "Unknown error")}
        return {
            "country": data.get("country"), "country_code": data.get("countryCode"),
            "region": data.get("regionName"), "city": data.get("city"),
            "zip": data.get("zip"), "lat": data.get("lat"), "lon": data.get("lon"),
            "timezone": data.get("timezone"), "isp": data.get("isp"),
            "org": data.get("org"), "asn": data.get("as"),
            "reverse_dns": data.get("reverse"), "mobile": data.get("mobile"),
            "proxy": data.get("proxy"), "hosting": data.get("hosting"),
        }
    except requests.RequestException as e:
        return {"error": str(e)}


def _reverse_dns(ip: str) -> str:
    try:
        return socket.gethostbyaddr(ip)[0]
    except (socket.herror, socket.gaierror):
        return ""


def _abuseipdb(ip: str) -> dict:
    key = get_key("abuseipdb")
    if not key:
        return {"available": False, "reason": "AbuseIPDB key not configured."}
    try:
        r = requests.get("https://api.abuseipdb.com/api/v2/check",
                         params={"ipAddress": ip, "maxAgeInDays": 90, "verbose": ""},
                         headers={"Key": key, "Accept": "application/json"}, timeout=10)
        if r.status_code == 401:
            return {"available": False, "reason": "Invalid AbuseIPDB key."}
        r.raise_for_status()
        d = r.json().get("data", {})
        return {
            "available": True,
            "abuse_confidence_score": d.get("abuseConfidenceScore"),
            "total_reports": d.get("totalReports"),
            "num_distinct_users": d.get("numDistinctUsers"),
            "last_reported": d.get("lastReportedAt"),
            "usage_type": d.get("usageType"),
            "domain": d.get("domain"),
            "is_tor": d.get("isTor"),
            "is_whitelisted": d.get("isWhitelisted"),
        }
    except requests.RequestException as e:
        return {"available": False, "reason": str(e)}


def _shodan(ip: str) -> dict:
    key = get_key("shodan")
    if not key:
        return {"available": False, "reason": "Shodan key not configured."}
    try:
        r = requests.get(f"https://api.shodan.io/shodan/host/{ip}",
                         params={"key": key}, timeout=15)
        if r.status_code == 401:
            return {"available": False, "reason": "Invalid Shodan key."}
        if r.status_code == 404:
            return {"available": True, "message": "IP not in Shodan database."}
        r.raise_for_status()
        d = r.json()
        return {
            "available": True,
            "os": d.get("os"),
            "hostnames": d.get("hostnames", []),
            "ports": d.get("ports", []),
            "vulns": d.get("vulns", []),
            "tags": d.get("tags", []),
            "services": [{"port": s.get("port"), "transport": s.get("transport"),
                          "product": s.get("product"), "version": s.get("version"),
                          "banner": (s.get("data", "")[:200])} for s in d.get("data", [])[:20]]
        }
    except requests.RequestException as e:
        return {"available": False, "reason": str(e)}


def _virustotal_ip(ip: str) -> dict:
    key = get_key("virustotal")
    if not key:
        return {"available": False, "reason": "VirusTotal key not configured."}
    try:
        r = requests.get(f"https://www.virustotal.com/api/v3/ip_addresses/{ip}",
                         headers={"x-apikey": key}, timeout=10)
        if r.status_code == 401:
            return {"available": False, "reason": "Invalid VT key."}
        r.raise_for_status()
        d = r.json().get("data", {}).get("attributes", {})
        stats = d.get("last_analysis_stats", {})
        return {
            "available": True,
            "reputation": d.get("reputation"),
            "malicious": stats.get("malicious", 0),
            "suspicious": stats.get("suspicious", 0),
            "harmless": stats.get("harmless", 0),
            "country": d.get("country"),
            "as_owner": d.get("as_owner"),
        }
    except requests.RequestException as e:
        return {"available": False, "reason": str(e)}


def run(target: str, mode: str = "basic", check_shodan: bool = False,
        check_virustotal: bool = False) -> dict:
    """IP investigation.

    mode: 'basic' (geo + rDNS) or 'advanced' (+ AbuseIPDB + Shodan + VirusTotal)
    """
    target = (target or "").strip()
    if not target:
        return {"error": "IP address required."}

    try:
        ipaddress.ip_address(target)
        ip = target
    except ValueError:
        try:
            ip = socket.gethostbyname(target)
        except socket.gaierror:
            return {"error": f"Could not resolve: {target}"}

    geo = _geolocate(ip)
    ptr = _reverse_dns(ip)

    out = {
        "target": target,
        "ip": ip,
        "reverse_dns": ptr,
        "geolocation": geo,
        "mode": mode,
    }

    if mode == "advanced":
        out["abuse_reports"] = _abuseipdb(ip)
        out["shodan"] = _shodan(ip)
        out["virustotal"] = _virustotal_ip(ip)
    else:
        out["abuse_reports"] = _abuseipdb(ip)  # cheap, try anyway
        if check_shodan:
            out["shodan"] = _shodan(ip)
        if check_virustotal:
            out["virustotal"] = _virustotal_ip(ip)

    out["summary"] = (f"{ip} | {geo.get('city', '?')}, {geo.get('country', '?')} | "
                      f"{geo.get('isp', 'Unknown ISP')}")
    return out
