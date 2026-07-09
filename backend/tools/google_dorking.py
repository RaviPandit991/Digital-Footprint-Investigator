"""Google Dorking - build advanced search queries + optional live Google CSE search."""
import requests
from urllib.parse import quote_plus
from backend.config import get_key


DORK_TEMPLATES = {
    "PDF files":         'site:{t} filetype:pdf',
    "Excel spreadsheets": 'site:{t} filetype:xls OR filetype:xlsx',
    "Word docs":         'site:{t} filetype:doc OR filetype:docx',
    "Config files":      'site:{t} (filetype:conf OR filetype:config OR filetype:ini)',
    "Log files":         'site:{t} filetype:log',
    "Backup files":      'site:{t} (filetype:bak OR filetype:old OR filetype:backup)',
    "SQL dumps":         'site:{t} filetype:sql',
    "Environment files": 'site:{t} filetype:env OR inurl:.env',
    "Git exposure":      'site:{t} inurl:.git',
    "Login pages":       'site:{t} (inurl:login OR inurl:signin OR inurl:admin)',
    "Directory listing": 'site:{t} intitle:"index of"',
    "Error messages":    'site:{t} (intext:"sql syntax" OR intext:"warning:" OR intext:"stack trace")',
    "Employee info":     'site:{t} (intext:"email" OR intext:"phone" OR intext:"@{t}")',
    "Password references": 'site:{t} (intext:password OR intext:passwd OR intext:credentials)',
    "API keys":          'site:{t} (intext:"api_key" OR intext:"apikey" OR intext:"secret_key")',
    "Subdomain search":  'site:*.{t}',
    "Pastebin mentions": 'site:pastebin.com "{t}"',
    "GitHub mentions":   'site:github.com "{t}"',
}


def _run_google_cse(query: str) -> dict:
    """Execute a live search using Google Custom Search API (requires key + engine ID)."""
    key = get_key("google_cse")
    cx = get_key("google_cx")
    if not (key and cx):
        return {"available": False, "reason": "Google CSE key/CX not configured. Configure in Authentication tab."}
    try:
        r = requests.get("https://www.googleapis.com/customsearch/v1",
                         params={"key": key, "cx": cx, "q": query, "num": 10},
                         timeout=10)
        if r.status_code == 400:
            return {"available": False, "reason": "Bad Google CSE request (check key/CX)."}
        r.raise_for_status()
        data = r.json()
        items = data.get("items", [])
        return {
            "available": True,
            "total_results": data.get("searchInformation", {}).get("totalResults"),
            "results": [{"title": i.get("title"), "link": i.get("link"),
                         "snippet": i.get("snippet")} for i in items]
        }
    except requests.RequestException as e:
        return {"available": False, "reason": str(e)}


def run(target: str) -> dict:
    q = (target or "").strip()
    if not q:
        return {"error": "Target domain or search query required."}

    # If it looks like a domain, generate dork templates. Otherwise treat as raw query.
    is_domain = "." in q and " " not in q

    dorks = {}
    if is_domain:
        domain = q.replace("http://", "").replace("https://", "").split("/")[0]
        for name, tmpl in DORK_TEMPLATES.items():
            dork_query = tmpl.format(t=domain)
            dorks[name] = {
                "query": dork_query,
                "google_url": f"https://www.google.com/search?q={quote_plus(dork_query)}",
                "duckduckgo_url": f"https://duckduckgo.com/?q={quote_plus(dork_query)}",
            }
        primary_query = f"site:{domain}"
    else:
        primary_query = q
        dorks["Raw query"] = {
            "query": q,
            "google_url": f"https://www.google.com/search?q={quote_plus(q)}",
            "duckduckgo_url": f"https://duckduckgo.com/?q={quote_plus(q)}",
        }

    live = _run_google_cse(primary_query)

    return {
        "target": q,
        "mode": "domain-dorks" if is_domain else "raw-query",
        "dorks": dorks,
        "live_results": live,
        "summary": f"Generated {len(dorks)} dork(s)."
                   + (f" Live results available." if live.get("available") else " Configure Google CSE key for live results.")
    }
