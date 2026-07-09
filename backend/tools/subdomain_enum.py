"""Subdomain enumeration via crt.sh certificate transparency logs (no API key)."""
import requests


def run(target: str) -> dict:
    target = (target or "").strip().lower()
    if not target:
        return {"error": "Domain required."}
    target = target.replace("http://", "").replace("https://", "").split("/")[0]

    url = f"https://crt.sh/?q=%25.{target}&output=json"
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "DFI/1.0"})
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        return {"error": f"crt.sh request failed: {e}"}
    except ValueError:
        return {"error": "crt.sh returned invalid JSON (rate limited?)."}

    subdomains = set()
    for entry in data:
        name = entry.get("name_value", "")
        for line in name.split("\n"):
            line = line.strip().lower()
            if line and line.endswith(target) and "*" not in line:
                subdomains.add(line)

    sub_list = sorted(subdomains)
    return {
        "target": target,
        "source": "crt.sh (Certificate Transparency)",
        "count": len(sub_list),
        "subdomains": sub_list,
        "summary": f"Found {len(sub_list)} subdomain(s) via certificate logs."
    }
