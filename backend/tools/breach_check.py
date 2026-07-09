"""Data breach check via HaveIBeenPwned + Pwned Passwords (k-anonymity)."""
import hashlib
import requests
from backend.config import get_key


def _check_password_pwned(password: str) -> dict:
    """K-anonymity check via Pwned Passwords (no API key needed)."""
    sha1 = hashlib.sha1(password.encode()).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    try:
        r = requests.get(f"https://api.pwnedpasswords.com/range/{prefix}",
                         timeout=8, headers={"User-Agent": "DFI/1.0"})
        r.raise_for_status()
        for line in r.text.splitlines():
            hash_suffix, count = line.split(":")
            if hash_suffix.strip() == suffix:
                return {"pwned": True, "seen_count": int(count),
                        "message": f"This password has appeared in {count} data breaches!"}
        return {"pwned": False, "seen_count": 0, "message": "Password not found in known breaches."}
    except requests.RequestException as e:
        return {"error": str(e)}


def _check_account_breaches(account: str) -> dict:
    """Full HIBP breach lookup for an email/account (requires API key)."""
    key = get_key("hibp")
    if not key:
        return {"available": False,
                "reason": "HIBP API key required for account breach lookup. Configure in Authentication tab.",
                "fallback": f"You can manually check at https://haveibeenpwned.com/account/{account}"}
    try:
        r = requests.get(f"https://haveibeenpwned.com/api/v3/breachedaccount/{account}",
                         params={"truncateResponse": "false"},
                         headers={"hibp-api-key": key, "User-Agent": "DFI/1.0"},
                         timeout=10)
        if r.status_code == 404:
            return {"available": True, "count": 0, "breaches": []}
        if r.status_code == 401:
            return {"available": False, "reason": "Invalid HIBP API key."}
        r.raise_for_status()
        breaches = r.json()
        return {
            "available": True,
            "count": len(breaches),
            "breaches": [{
                "name": b.get("Name"),
                "title": b.get("Title"),
                "date": b.get("BreachDate"),
                "pwn_count": b.get("PwnCount"),
                "data_classes": b.get("DataClasses", []),
                "description": b.get("Description", "")[:200] + "..."
            } for b in breaches]
        }
    except requests.RequestException as e:
        return {"available": False, "reason": str(e)}


def run(target: str) -> dict:
    q = (target or "").strip()
    if not q:
        return {"error": "Email, username, or password required."}

    # Heuristic: if it looks like a common password (no @, short, has letters)
    is_email = "@" in q
    if is_email:
        result = _check_account_breaches(q)
        return {
            "target": q,
            "type": "account",
            "result": result,
            "summary": f"Account: {'in ' + str(result.get('count', 0)) + ' breaches' if result.get('available') else result.get('reason')}"
        }
    else:
        # Try both: account lookup AND password lookup
        password_result = _check_password_pwned(q)
        return {
            "target": "[password-masked]",
            "type": "password",
            "result": password_result,
            "summary": password_result.get("message", password_result.get("error", "Check complete"))
        }
