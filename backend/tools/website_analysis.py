"""Website analysis - tech stack, headers, robots.txt, sitemap, trackers."""
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


TECH_SIGNATURES = {
    # CMS
    "WordPress":   [r"wp-content", r"wp-includes", r'content="WordPress'],
    "Drupal":      [r"Drupal\.settings", r'content="Drupal'],
    "Joomla":      [r'content="Joomla'],
    "Ghost":       [r"ghost-", r"generator.*Ghost"],
    "Magento":     [r"Mage\.Cookies", r"/skin/frontend/"],
    "Shopify":     [r"cdn\.shopify\.com", r"Shopify\.theme"],
    "Wix":         [r"wixstatic\.com", r"wix\.com"],
    "Squarespace": [r"squarespace"],
    "Webflow":     [r"webflow\.io", r"webflow\.com"],
    "HubSpot CMS": [r"hs-scripts", r"hubspotusercontent"],
    "Contentful":  [r"contentful\.com"],
    # JS Frameworks
    "React":       [r"__NEXT_DATA__", r"react-root", r"data-reactroot", r"_react"],
    "Next.js":     [r"__NEXT_DATA__", r"_next/static"],
    "Vue.js":      [r"__vue__", r"vue\.js", r'data-v-'],
    "Nuxt.js":     [r"__NUXT__", r"_nuxt/"],
    "Angular":     [r"ng-version", r"ng-app", r"angular\.js"],
    "Svelte":      [r"__svelte", r"svelte-"],
    "Ember":       [r"ember\.js", r"ember-"],
    "Backbone":    [r"backbone\.js"],
    "jQuery":      [r"jquery"],
    "Alpine.js":   [r"alpine.*\.js", r"x-data"],
    # CSS Frameworks
    "Bootstrap":   [r"bootstrap"],
    "Tailwind":    [r"tailwind"],
    "Bulma":       [r"bulma"],
    "Foundation":  [r"foundation\.css"],
    "Material UI": [r"material-ui", r"mui-"],
    "Chakra UI":   [r"chakra-ui"],
    # Servers / CDNs
    "Cloudflare":  [r"cloudflare", r"__cf_bm"],
    "Amazon CloudFront": [r"cloudfront"],
    "Fastly":      [r"fastly"],
    "Akamai":      [r"akamai"],
    "Vercel":      [r"vercel", r"__vercel"],
    "Netlify":     [r"netlify"],
    "Nginx":       [r"nginx"],
    "Apache":      [r"apache"],
    "IIS":         [r"iis"],
    # Analytics / Trackers
    "Google Analytics": [r"google-analytics\.com/analytics\.js", r"gtag\(", r"UA-\d"],
    "Google Analytics 4": [r"G-[A-Z0-9]+", r"gtag/js\?id=G-"],
    "Google Tag Manager": [r"googletagmanager", r"gtm\.js"],
    "Facebook Pixel": [r"fbq\(", r"connect\.facebook\.net/.*fbevents"],
    "LinkedIn Insight": [r"linkedin\.com/insight", r"snap\.licdn\.com"],
    "Twitter Pixel": [r"analytics\.twitter\.com", r"static\.ads-twitter\.com"],
    "TikTok Pixel": [r"analytics\.tiktok\.com"],
    "Hotjar":      [r"hotjar", r"hj\("],
    "Mixpanel":    [r"mixpanel"],
    "Segment":     [r"segment\.com", r"analytics\.js"],
    "Amplitude":   [r"amplitude"],
    "Adobe Analytics": [r"adobedtm", r"sc\.omtrdc\.net"],
    "Matomo":      [r"matomo", r"piwik"],
    "Plausible":   [r"plausible\.io"],
    "Fathom":      [r"usefathom"],
    "Yandex Metrika": [r"mc\.yandex\.ru"],
    # Payment
    "Stripe":      [r"js\.stripe\.com"],
    "PayPal":      [r"paypal\.com/sdk", r"paypalobjects"],
    "Braintree":   [r"braintreegateway"],
    "Square":      [r"squareup"],
    # Support / Chat
    "Intercom":    [r"intercom\.io", r"widget\.intercom\.io"],
    "Zendesk":     [r"zendesk"],
    "Drift":       [r"drift\.com"],
    "Crisp":       [r"crisp\.chat"],
    "Tawk.to":     [r"tawk\.to"],
    "HubSpot":     [r"hs-scripts", r"hs-analytics"],
    "LiveChat":    [r"livechatinc"],
    # Ads
    "Google AdSense": [r"googlesyndication", r"adsbygoogle"],
    "DoubleClick": [r"doubleclick\.net"],
    "Amazon Ads":  [r"amazon-adsystem"],
    # Security
    "reCAPTCHA":   [r"recaptcha"],
    "hCaptcha":    [r"hcaptcha"],
    "Cloudflare Turnstile": [r"turnstile"],
}

TRACKER_PATTERNS = {
    "Google Analytics", "Google Analytics 4", "Google Tag Manager",
    "Facebook Pixel", "LinkedIn Insight", "Twitter Pixel", "TikTok Pixel",
    "Hotjar", "Mixpanel", "Segment", "Amplitude", "Adobe Analytics",
    "Matomo", "Plausible", "Fathom", "Yandex Metrika",
    "Google AdSense", "DoubleClick", "Amazon Ads"
}

SECURITY_HEADERS_LIST = [
    "Content-Security-Policy", "Strict-Transport-Security", "X-Frame-Options",
    "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy",
    "X-XSS-Protection", "Cross-Origin-Opener-Policy", "Cross-Origin-Embedder-Policy",
    "Cross-Origin-Resource-Policy"
]


def _fingerprint(text: str, headers: dict) -> list:
    tech = set()
    blob = text + " " + " ".join(f"{k}: {v}" for k, v in headers.items())
    for name, patterns in TECH_SIGNATURES.items():
        for p in patterns:
            if re.search(p, blob, re.IGNORECASE):
                tech.add(name)
                break
    if "X-Powered-By" in headers:
        tech.add(headers["X-Powered-By"])
    return sorted(tech)


def _fetch_robots(base_url: str) -> dict:
    url = urljoin(base_url, "/robots.txt")
    try:
        r = requests.get(url, timeout=6, headers={"User-Agent": "DFI/1.0"})
        if r.status_code != 200:
            return {"exists": False, "status": r.status_code}
        text = r.text[:8000]
        disallows = [line.split(":", 1)[1].strip()
                     for line in text.splitlines()
                     if line.lower().startswith("disallow:") and ":" in line]
        sitemaps = [line.split(":", 1)[1].strip()
                    for line in text.splitlines()
                    if line.lower().startswith("sitemap:")]
        return {"exists": True, "url": url, "disallow_count": len(disallows),
                "disallowed_paths": disallows[:30], "sitemaps": sitemaps,
                "raw_preview": text[:1000]}
    except requests.RequestException as e:
        return {"exists": False, "error": str(e)}


def _fetch_sitemap(sitemap_url: str) -> dict:
    try:
        r = requests.get(sitemap_url, timeout=8, headers={"User-Agent": "DFI/1.0"})
        if r.status_code != 200:
            return {"url": sitemap_url, "status": r.status_code, "urls": []}
        # Very basic extraction — pull all <loc> tags
        urls = re.findall(r"<loc>\s*([^<]+)\s*</loc>", r.text)
        return {"url": sitemap_url, "status": 200, "url_count": len(urls),
                "urls": urls[:50]}
    except requests.RequestException as e:
        return {"url": sitemap_url, "error": str(e)}


def run(target: str, mode: str = "basic", fetch_robots: bool = True,
        fetch_sitemap: bool = False) -> dict:
    """Website analysis.

    mode: 'basic' (tech + headers) or 'advanced' (+ robots + sitemap + trackers separated)
    fetch_robots: fetch and parse /robots.txt
    fetch_sitemap: also fetch sitemaps referenced from robots
    """
    url = (target or "").strip()
    if not url:
        return {"error": "URL required."}
    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    try:
        r = requests.get(url, timeout=12,
                         headers={"User-Agent": "Mozilla/5.0 DFI/1.0"},
                         allow_redirects=True)
    except requests.RequestException as e:
        return {"error": f"Request failed: {e}"}

    soup = BeautifulSoup(r.text, "html.parser")
    parsed = urlparse(r.url)

    server_info = {h: r.headers[h] for h in
                   ["Server", "X-Powered-By", "X-AspNet-Version",
                    "X-Generator", "X-Drupal-Cache", "Via", "X-Framework"]
                   if h in r.headers}

    security_headers = {h: r.headers.get(h, "MISSING") for h in SECURITY_HEADERS_LIST}
    missing_security = [h for h, v in security_headers.items() if v == "MISSING"]

    cookies = [{"name": c.name, "domain": c.domain, "secure": c.secure,
                "httponly": bool(c._rest.get("HttpOnly")) if hasattr(c, "_rest") else False}
               for c in r.cookies]

    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    meta_desc = soup.find("meta", attrs={"name": "description"})
    description = meta_desc["content"] if meta_desc and meta_desc.get("content") else ""

    og = {m["property"]: m.get("content", "") for m
          in soup.find_all("meta", property=re.compile(r"^og:"))}

    tech = _fingerprint(r.text, dict(r.headers))
    trackers = [t for t in tech if t in TRACKER_PATTERNS]

    scripts = list({s.get("src") for s in soup.find_all("script", src=True)
                    if s.get("src")})[:30]

    out = {
        "target": url, "final_url": r.url, "status_code": r.status_code,
        "title": title, "description": description,
        "server_headers": server_info,
        "security_headers": security_headers,
        "missing_security_headers": missing_security,
        "cookies": cookies, "open_graph": og,
        "technologies": tech,
        "trackers_detected": trackers,
        "scripts_external": scripts,
        "mode": mode,
    }

    if mode == "advanced" or fetch_robots:
        out["robots_txt"] = _fetch_robots(r.url)

    if mode == "advanced" or fetch_sitemap:
        sitemap_urls = out.get("robots_txt", {}).get("sitemaps") or [urljoin(r.url, "/sitemap.xml")]
        out["sitemaps"] = [_fetch_sitemap(s) for s in sitemap_urls[:3]]

    out["summary"] = (f"{r.status_code} | {parsed.netloc} | "
                      f"Tech: {', '.join(tech[:5]) or 'None'} | "
                      f"{len(trackers)} tracker(s) | "
                      f"{len(missing_security)}/{len(SECURITY_HEADERS_LIST)} security headers missing")
    return out
