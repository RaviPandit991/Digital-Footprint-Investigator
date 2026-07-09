"""Website analysis - tech stack fingerprinting, headers, cookies."""
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


TECH_SIGNATURES = {
    "WordPress":   [r"wp-content", r"wp-includes", r'name="generator" content="WordPress'],
    "Drupal":      [r"Drupal.settings", r'name="generator" content="Drupal'],
    "Joomla":      [r'name="generator" content="Joomla'],
    "Shopify":     [r"cdn.shopify.com", r"Shopify.theme"],
    "Wix":         [r"wixstatic.com", r"wix\.com"],
    "Squarespace": [r"squarespace"],
    "React":       [r"__NEXT_DATA__", r"react-root", r"data-reactroot"],
    "Vue.js":      [r"__vue__", r"vue\.js", r'data-v-'],
    "Angular":     [r"ng-version", r"ng-app", r"angular\.js"],
    "jQuery":      [r"jquery"],
    "Bootstrap":   [r"bootstrap"],
    "Tailwind":    [r"tailwind"],
    "Google Analytics": [r"google-analytics\.com", r"gtag\("],
    "Google Tag Manager": [r"googletagmanager"],
    "Cloudflare":  [r"cloudflare"],
    "reCAPTCHA":   [r"recaptcha"],
    "Stripe":      [r"js\.stripe\.com"],
    "PayPal":      [r"paypal\.com/sdk"],
    "Intercom":    [r"intercom\.io"],
    "HubSpot":     [r"hs-scripts", r"hubspot"],
}

SERVER_HEADERS_OF_INTEREST = [
    "Server", "X-Powered-By", "X-AspNet-Version", "X-AspNetMvc-Version",
    "X-Generator", "X-Drupal-Cache", "X-Pingback", "Via", "X-Framework"
]


def _fingerprint(text: str, headers: dict) -> list:
    tech = set()
    header_blob = " ".join(f"{k}: {v}" for k, v in headers.items())
    combined = text + " " + header_blob
    for name, patterns in TECH_SIGNATURES.items():
        for p in patterns:
            if re.search(p, combined, re.IGNORECASE):
                tech.add(name)
                break
    # Extra: check X-Powered-By
    if "X-Powered-By" in headers:
        tech.add(headers["X-Powered-By"])
    return sorted(tech)


def run(target: str) -> dict:
    url = (target or "").strip()
    if not url:
        return {"error": "URL required."}
    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    try:
        r = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0 DFI/1.0"},
                         allow_redirects=True)
    except requests.RequestException as e:
        return {"error": f"Request failed: {e}"}

    soup = BeautifulSoup(r.text, "html.parser")
    parsed = urlparse(r.url)

    # Server headers of interest
    server_info = {h: r.headers[h] for h in SERVER_HEADERS_OF_INTEREST if h in r.headers}

    # Security headers
    security_headers = {}
    for h in ["Content-Security-Policy", "Strict-Transport-Security", "X-Frame-Options",
              "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy",
              "X-XSS-Protection"]:
        security_headers[h] = r.headers.get(h, "MISSING")

    # Cookies
    cookies = [{"name": c.name, "domain": c.domain, "secure": c.secure,
                "httponly": bool(c._rest.get("HttpOnly")) if hasattr(c, "_rest") else False}
               for c in r.cookies]

    # Title, description
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    meta_desc = soup.find("meta", attrs={"name": "description"})
    description = meta_desc["content"] if meta_desc and meta_desc.get("content") else ""

    # Social meta
    og = {}
    for m in soup.find_all("meta", property=re.compile(r"^og:")):
        og[m["property"]] = m.get("content", "")

    # Fingerprint
    tech = _fingerprint(r.text, dict(r.headers))

    # External scripts / links
    scripts = list({s.get("src") for s in soup.find_all("script", src=True) if s.get("src")})[:30]

    return {
        "target": url,
        "final_url": r.url,
        "status_code": r.status_code,
        "title": title,
        "description": description,
        "server_headers": server_info,
        "security_headers": security_headers,
        "cookies": cookies,
        "open_graph": og,
        "technologies": tech,
        "scripts_external": scripts,
        "summary": f"{r.status_code} | {parsed.netloc} | Tech: {', '.join(tech[:5]) or 'None detected'}"
    }
