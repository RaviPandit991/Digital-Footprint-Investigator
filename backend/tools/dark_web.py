"""Dark web monitoring - search Ahmia.fi Tor index (no Tor needed, they mirror onion results)."""
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus


def run(target: str) -> dict:
    q = (target or "").strip()
    if not q:
        return {"error": "Search keyword required."}

    url = f"https://ahmia.fi/search/?q={quote_plus(q)}"
    try:
        r = requests.get(url, timeout=15,
                         headers={"User-Agent": "Mozilla/5.0 DFI/1.0"})
        r.raise_for_status()
    except requests.RequestException as e:
        return {"error": f"Ahmia request failed: {e}"}

    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    for li in soup.select("li.result")[:30]:
        title_el = li.find("h4")
        link_el = title_el.find("a") if title_el else None
        desc_el = li.find("p")
        cite_el = li.find("cite")
        if link_el:
            results.append({
                "title": link_el.get_text(strip=True),
                "onion_url": link_el.get("href", ""),
                "description": desc_el.get_text(strip=True)[:300] if desc_el else "",
                "domain": cite_el.get_text(strip=True) if cite_el else "",
            })

    return {
        "target": q,
        "source": "Ahmia.fi (Tor index)",
        "count": len(results),
        "results": results,
        "note": "Onion URLs require the Tor Browser to access. Ahmia mirrors indexed content only.",
        "summary": f"Found {len(results)} dark web result(s) mentioning '{q}'."
    }
