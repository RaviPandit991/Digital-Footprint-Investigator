"""Authentication tool - manage API keys for external services."""
from backend.config import load_keys, save_keys, DEFAULT_KEYS

SERVICE_INFO = {
    "hibp":       {"name": "HaveIBeenPwned", "used_by": ["Data Breach Check"], "signup": "https://haveibeenpwned.com/API/Key"},
    "shodan":     {"name": "Shodan",         "used_by": ["IP Investigation"],   "signup": "https://account.shodan.io/register"},
    "virustotal": {"name": "VirusTotal",     "used_by": ["Domain / IP Investigation"], "signup": "https://www.virustotal.com/gui/join-us"},
    "hunter":     {"name": "Hunter.io",      "used_by": ["Email Investigation"], "signup": "https://hunter.io/users/sign_up"},
    "abuseipdb":  {"name": "AbuseIPDB",      "used_by": ["IP Investigation"], "signup": "https://www.abuseipdb.com/register"},
    "google_cse": {"name": "Google Custom Search (key)", "used_by": ["Google Dorking"], "signup": "https://developers.google.com/custom-search/v1/introduction"},
    "google_cx":  {"name": "Google Custom Search (engine ID)", "used_by": ["Google Dorking"], "signup": "https://programmablesearchengine.google.com/"},
    "tineye":     {"name": "TinEye",         "used_by": ["Reverse Image Search"], "signup": "https://services.tineye.com/TinEyeAPI"},
}


def get_status() -> dict:
    """Return which keys are configured."""
    keys = load_keys()
    status = {}
    for k, info in SERVICE_INFO.items():
        status[k] = {
            "name": info["name"],
            "used_by": info["used_by"],
            "signup": info["signup"],
            "configured": bool(keys.get(k, "")),
        }
    return {
        "services": status,
        "summary": f"{sum(1 for s in status.values() if s['configured'])}/{len(status)} services configured."
    }


def update(service: str, key: str) -> dict:
    if service not in DEFAULT_KEYS:
        return {"error": f"Unknown service: {service}. Valid: {list(DEFAULT_KEYS.keys())}"}
    keys = load_keys()
    keys[service] = key.strip()
    save_keys(keys)
    return {"service": service, "configured": bool(keys[service]),
            "summary": f"{SERVICE_INFO[service]['name']} key {'set' if key.strip() else 'cleared'}."}


def run(target: str = "") -> dict:
    """Default action: return status of all keys."""
    return get_status()
