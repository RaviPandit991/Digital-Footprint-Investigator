"""Basic web crawler - collect links, forms, emails, external hosts."""
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def run(target: str, max_pages: int = 15, max_depth: int = 2) -> dict:
    target = (target or "").strip().rstrip("/")
    if not target:
        return {"error": "URL required."}
    if not target.startswith(("http://", "https://")):
        target = "http://" + target

    base_host = urlparse(target).netloc
    visited = set()
    to_visit = deque([(target, 0)])
    all_links = set()
    external_hosts = set()
    emails = set()
    forms = []
    headers = {"User-Agent": "DFI/1.0"}

    while to_visit and len(visited) < max_pages:
        url, depth = to_visit.popleft()
        if url in visited or depth > max_depth:
            continue
        visited.add(url)

        try:
            r = requests.get(url, timeout=8, headers=headers, allow_redirects=True)
            if "text/html" not in r.headers.get("Content-Type", ""):
                continue
        except requests.RequestException:
            continue

        soup = BeautifulSoup(r.text, "html.parser")

        # Emails
        for match in EMAIL_RE.findall(r.text):
            emails.add(match)

        # Forms
        for form in soup.find_all("form"):
            forms.append({
                "action": urljoin(url, form.get("action", "")),
                "method": form.get("method", "GET").upper(),
                "inputs": [i.get("name") for i in form.find_all("input") if i.get("name")]
            })

        # Links
        for a in soup.find_all("a", href=True):
            link = urljoin(url, a["href"]).split("#")[0]
            parsed = urlparse(link)
            if parsed.scheme not in ("http", "https"):
                continue
            all_links.add(link)
            if parsed.netloc == base_host:
                if link not in visited and len(visited) + len(to_visit) < max_pages:
                    to_visit.append((link, depth + 1))
            else:
                external_hosts.add(parsed.netloc)

    return {
        "target": target,
        "pages_crawled": len(visited),
        "total_links": len(all_links),
        "internal_links": sorted([l for l in all_links if urlparse(l).netloc == base_host])[:50],
        "external_hosts": sorted(external_hosts),
        "emails": sorted(emails),
        "forms": forms[:20],
        "summary": f"Crawled {len(visited)} page(s), found {len(all_links)} link(s), {len(emails)} email(s)."
    }
