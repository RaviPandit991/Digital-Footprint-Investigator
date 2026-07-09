"""Email investigation - syntax, MX, disposable, gravatar, HIBP, deep checks."""
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
    "dispostable.com", "mytemp.email", "mailnesia.com", "spam4.me",
    "tempinbox.com", "throwaway.email", "guerrillamail.net", "grr.la",
    "mytrashmail.com", "10minutemail.net", "mailcatch.com", "temp-mail.io",
    "burnermail.io", "dropmail.me", "temporarymail.com", "mohmal.com"
}

FREE_PROVIDERS = {
    "gmail.com", "googlemail.com", "yahoo.com", "yahoo.co.uk", "outlook.com",
    "hotmail.com", "live.com", "aol.com", "icloud.com", "me.com", "mac.com",
    "protonmail.com", "proton.me", "tutanota.com", "yandex.com", "yandex.ru",
    "mail.ru", "zoho.com", "gmx.com", "mail.com", "fastmail.com"
}


def _check_mx(domain: str) -> list:
    try:
        answers = dns.resolver.resolve(domain, "MX", lifetime=5)
        return sorted([f"{r.preference} {r.exchange}" for r in answers])
    except Exception:
        return []


def _gravatar(email: str) -> dict:
    email_hash = hashlib.md5(email.lower().strip().encode()).hexdigest()
    profile_url = f"https://www.gravatar.com/avatar/{email_hash}?d=404"
    avatar_url = f"https://www.gravatar.com/avatar/{email_hash}"
    profile_json = f"https://www.gravatar.com/{email_hash}.json"
    try:
        r = requests.get(profile_url, timeout=6, allow_redirects=False)
        has_avatar = r.status_code == 200
    except requests.RequestException:
        has_avatar = None

    profile_data = None
    if has_avatar:
        try:
            r = requests.get(profile_json, timeout=6, headers={"User-Agent": "DFI/1.0"})
            if r.status_code == 200:
                data = r.json()
                if data.get("entry"):
                    e = data["entry"][0]
                    profile_data = {
                        "display_name": e.get("displayName"),
                        "name": e.get("name"),
                        "location": e.get("currentLocation"),
                        "bio": (e.get("aboutMe") or "")[:200],
                        "urls": [{"title": u.get("title"), "value": u.get("value")}
                                 for u in e.get("urls", [])],
                        "accounts": [{"domain": a.get("domain"), "url": a.get("url"),
                                      "username": a.get("username")}
                                     for a in e.get("accounts", [])],
                    }
        except (requests.RequestException, ValueError):
            pass

    return {"hash": email_hash, "has_avatar": has_avatar,
            "avatar_url": avatar_url, "profile": profile_data}


def _hibp_breaches(email: str) -> dict:
    key = get_key("hibp")
    if not key:
        return {"available": False, "reason": "HIBP API key not configured."}
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
            "available": True, "count": len(breaches),
            "breaches": [{"name": b.get("Name"), "date": b.get("BreachDate"),
                          "pwn_count": b.get("PwnCount"),
                          "data_classes": b.get("DataClasses", [])} for b in breaches]
        }
    except requests.RequestException as e:
        return {"available": False, "reason": f"Request failed: {e}"}


def _hunter_verify(email: str) -> dict:
    key = get_key("hunter")
    if not key:
        return {"available": False, "reason": "Hunter.io key not configured."}
    try:
        r = requests.get("https://api.hunter.io/v2/email-verifier",
                         params={"email": email, "api_key": key}, timeout=10)
        if r.status_code == 401:
            return {"available": False, "reason": "Invalid Hunter.io key."}
        r.raise_for_status()
        d = r.json().get("data", {})
        return {"available": True, "status": d.get("status"), "result": d.get("result"),
                "score": d.get("score"), "regexp": d.get("regexp"),
                "gibberish": d.get("gibberish"), "disposable": d.get("disposable"),
                "webmail": d.get("webmail"), "mx_records": d.get("mx_records"),
                "smtp_server": d.get("smtp_server"), "smtp_check": d.get("smtp_check"),
                "accept_all": d.get("accept_all"), "block": d.get("block"),
                "sources_count": len(d.get("sources", []))}
    except requests.RequestException as e:
        return {"available": False, "reason": str(e)}


def run(target: str, mode: str = "basic", check_gravatar: bool = True,
        check_hibp: bool = True, check_hunter: bool = False) -> dict:
    """Email investigation.

    mode: 'basic' (syntax + MX + disposable) or 'advanced' (+ full Gravatar profile + HIBP + Hunter)
    """
    email = (target or "").strip().lower()
    if not email:
        return {"error": "Email required."}

    valid_syntax = bool(EMAIL_RE.match(email))
    if not valid_syntax:
        return {"target": email, "valid_syntax": False, "error": "Invalid email format."}

    local, domain = email.split("@")
    mx = _check_mx(domain)
    disposable = domain in DISPOSABLE_DOMAINS
    is_free_provider = domain in FREE_PROVIDERS

    out = {
        "email": email,
        "local_part": local,
        "domain": domain,
        "valid_syntax": True,
        "deliverable": bool(mx),
        "mx_records": mx,
        "disposable": disposable,
        "free_provider": is_free_provider,
        "mode": mode,
    }

    if mode == "advanced" or check_gravatar:
        out["gravatar"] = _gravatar(email)
    if mode == "advanced" or check_hibp:
        out["breaches"] = _hibp_breaches(email)
    if mode == "advanced" or check_hunter:
        out["hunter"] = _hunter_verify(email)

    summary_parts = []
    summary_parts.append("Deliverable" if mx else "No MX")
    if disposable: summary_parts.append("DISPOSABLE")
    if is_free_provider: summary_parts.append("free provider")
    if out.get("breaches", {}).get("available"):
        summary_parts.append(f"{out['breaches']['count']} breaches")
    if out.get("gravatar", {}).get("has_avatar"):
        summary_parts.append("has Gravatar")
    out["summary"] = " | ".join(summary_parts)
    return out
