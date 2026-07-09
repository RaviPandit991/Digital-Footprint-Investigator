"""Web crawler with configurable depth, extractors, and robots.txt support."""
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from collections import deque

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"\+?\d[\d\-\s()]{7,}\d")
SOCIAL_RE = re.compile(r"(twitter\.com|facebook\.com|instagram\.com|linkedin\.com|"
                        r"github\.com|youtube\.com|tiktok\.com|reddit\.com)/[\w\-\.]+",
                        re.IGNORECASE)


def _load_robots(base_url: str):
    parser = RobotFileParser()
    try:
        parser.set_url(urljoin(base_url, "/robots.txt"))
        parser.read()
        return parser
    except Exception:
        return None


def run(target: str, max_pages: int = 15, max_depth: int = 2,
        respect_robots: bool = True, extract_emails: bool = True,
        extract_phones: bool = False, extract_social: bool = True,
        extract_js: bool = False) -> dict:
    """Crawl a website.

    max_pages: max pages to fetch
    max_depth: max link depth from start URL
    respect_robots: obey robots.txt
    extract_emails/phones/social/js: what to extract from each page
    """
    target = (target or "").strip().rstrip("/")
    if not target:
        return {"error": "URL required."}
    if not target.startswith(("http://", "https://")):
        target = "http://" + target

    max_pages = min(max(1, int(max_pages)), 100)
    max_depth = min(max(1, int(max_depth)), 5)

    base_host = urlparse(target).netloc
    robots = _load_robots(target) if respect_robots else None

    visited = set()
    to_visit = deque([(target, 0)])
    all_links = set()
    external_hosts = set()
    emails = set()
    phones = set()
    social = set()
    js_files = set()
    forms = []
    headers = {"User-Agent": "Mozilla/5.0 DFI/1.0"}

    while to_visit and len(visited) < max_pages:
        url, depth = to_visit.popleft()
        if url in visited or depth > max_depth:
            continue
        if robots and not robots.can_fetch("*", url):
            continue
        visited.add(url)

        try:
            r = requests.get(url, timeout=8, headers=headers, allow_redirects=True)
            if "text/html" not in r.headers.get("Content-Type", ""):
                continue
        except requests.RequestException:
            continue

        soup = BeautifulSoup(r.text, "html.parser")

        if extract_emails:
            emails.update(EMAIL_RE.findall(r.text))
        if extract_phones:
            phones.update(m.strip() for m in PHONE_RE.findall(r.text)
                          if len(m.replace(" ", "").replace("-", "")) >= 8)
        if extract_social:
            for m in SOCIAL_RE.findall(r.text):
                # findall returns just the platform part in tuples due to groups
                pass
            for match in SOCIAL_RE.finditer(r.text):
                social.add(match.group(0))

        for form in soup.find_all("form"):
            forms.append({
                "action": urljoin(url, form.get("action", "")),
                "method": form.get("method", "GET").upper(),
                "inputs": [i.get("name") for i in form.find_all(["input", "textarea", "select"])
                           if i.get("name")]
            })

        if extract_js:
            for s in soup.find_all("script", src=True):
                js_url = urljoin(url, s["src"])
                js_files.add(js_url)

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
        "pages_limit": max_pages,
        "depth_limit": max_depth,
        "respect_robots": respect_robots,
        "total_links": len(all_links),
        "internal_links": sorted([l for l in all_links if urlparse(l).netloc == base_host])[:80],
        "external_hosts": sorted(external_hosts),
        "emails": sorted(emails) if extract_emails else None,
        "phones": sorted(phones) if extract_phones else None,
        "social_profiles": sorted(social) if extract_social else None,
        "js_files": sorted(js_files)[:50] if extract_js else None,
        "forms": forms[:30],
        "summary": f"Crawled {len(visited)}/{max_pages} pages, "
                   f"{len(all_links)} links, "
                   f"{len(emails)} emails, {len(social)} social profiles."
    }
