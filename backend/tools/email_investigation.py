"""Email investigation - syntax, MX, disposable check, gravatar, HIBP breach check."""
import hashlib
import re
import requests
import dns.resolver
from backend.config import get_key

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

DISPOSABLE_DOMAINS = {
    "mailinator.com", "tempmail.com", "guerrillamail.com", "10minutemail.com",
    "throwawaymail.com", "yopmail.com", "trashmail.com", "getnada.com",
    "sharklasers.com", "temp-mail.org", "fakeinbox.com", "maildrop.cc",
    "dispostable.com", "mytemp.email", "mailnesia.com", "spam4.me"
}


def _check_mx(domain: str) -> list:
    try:
        answers = dns.resolver.resolve(domain, "MX", lifetime=5)
        return sorted([f"{r.preference} {r.exchange}" for r in answers])
    except Exception:
        return []


def _gravatar(email: str) -> dict:
    email_hash = hashlib.md5(email.lower().strip().encode()).hexdigest()
    url = f"https://www.gravatar.com/{email_hash}.json"
    profile_url = f"https://www.gravatar.com/avatar/{email_hash}?d=404"
    try:
        r = requests.get(profile_url, timeout=6, allow_redirects=False)
        has_avatar = r.status_code == 200
    except requests.RequestException:
        has_avatar = None
    return {"hash": email_hash, "has_avatar": has_avatar, "profile_api": url}


def _hibp_breaches(email: str) -> dict:
    key = get_key("hibp")
    if not key:
        return {"available": False, "reason": "HIBP API key not configured. Set it in the Authentication tab."}
    url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}?truncateResponse=false"
    try:
        r = requests.get(url, headers={"hibp-api-key": key, "User-Agent": "DFI/1.0"}, timeout=10)
        if r.status_code == 404:
            return {"available": True, "breaches": [], "count": 0}
        if r.status_code == 401:
            return {"available": False, "reason": "Invalid HIBP API key."}
        r.raise_for_status()
        breaches = r.json()
        return {
            "available": True,
            "count": len(breaches),
            "breaches": [{"name": b.get("Name"), "date": b.get("BreachDate"),
                          "data_classes": b.get("DataClasses", [])} for b in breaches]
        }
    except requests.RequestException as e:
        return {"available": False, "reason": f"Request failed: {e}"}


def run(target: str) -> dict:
    email = (target or "").strip().lower()
    if not email:
        return {"error": "Email required."}

    valid_syntax = bool(EMAIL_RE.match(email))
    if not valid_syntax:
        return {"target": email, "valid_syntax": False, "error": "Invalid email format."}

    domain = email.split("@")[1]
    mx = _check_mx(domain)
    disposable = domain in DISPOSABLE_DOMAINS
    gravatar = _gravatar(email)
    breaches = _hibp_breaches(email)

    return {
        "email": email,
        "domain": domain,
        "valid_syntax": True,
        "deliverable": bool(mx),
        "mx_records": mx,
        "disposable": disposable,
        "gravatar": gravatar,
        "breaches": breaches,
        "summary": f"{'Deliverable' if mx else 'No MX'} | {'Disposable' if disposable else 'Legit domain'} | "
                   f"{'Breaches: ' + str(breaches.get('count', '?')) if breaches.get('available') else 'HIBP unavailable'}"
    }
