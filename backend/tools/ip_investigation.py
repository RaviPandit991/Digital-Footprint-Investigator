"""IP investigation - geolocation, ASN, reverse DNS, blacklist check."""
import socket
import ipaddress
import requests
from backend.config import get_key


def _geolocate(ip: str) -> dict:
    """Uses ip-api.com free tier (no key needed, 45 req/min)."""
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}?fields=66846719", timeout=8)
        r.raise_for_status()
        data = r.json()
        if data.get("status") != "success":
            return {"error": data.get("message", "Unknown error")}
        return {
            "country": data.get("country"),
            "country_code": data.get("countryCode"),
            "region": data.get("regionName"),
            "city": data.get("city"),
            "zip": data.get("zip"),
            "lat": data.get("lat"),
            "lon": data.get("lon"),
            "timezone": data.get("timezone"),
            "isp": data.get("isp"),
            "org": data.get("org"),
            "asn": data.get("as"),
            "reverse_dns": data.get("reverse"),
            "mobile": data.get("mobile"),
            "proxy": data.get("proxy"),
            "hosting": data.get("hosting"),
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
                         params={"ipAddress": ip, "maxAgeInDays": 90},
                         headers={"Key": key, "Accept": "application/json"},
                         timeout=10)
        if r.status_code == 401:
            return {"available": False, "reason": "Invalid AbuseIPDB key."}
        r.raise_for_status()
        d = r.json().get("data", {})
        return {
            "available": True,
            "abuse_confidence_score": d.get("abuseConfidenceScore"),
            "total_reports": d.get("totalReports"),
            "last_reported": d.get("lastReportedAt"),
            "usage_type": d.get("usageType"),
        }
    except requests.RequestException as e:
        return {"available": False, "reason": str(e)}


def run(target: str) -> dict:
    target = (target or "").strip()
    if not target:
        return {"error": "IP address required."}

    # Accept hostnames too
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
    abuse = _abuseipdb(ip)

    return {
        "target": target,
        "ip": ip,
        "reverse_dns": ptr,
        "geolocation": geo,
        "abuse_reports": abuse,
        "summary": f"{ip} | {geo.get('city', '?')}, {geo.get('country', '?')} | {geo.get('isp', 'Unknown ISP')}"
    }
