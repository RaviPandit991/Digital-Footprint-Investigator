"""Subdomain enumeration - crt.sh + optional DNS bruteforce + live check."""
import socket
import requests
import dns.resolver
import dns.exception
from concurrent.futures import ThreadPoolExecutor, as_completed

COMMON_SUBS_SMALL = [
    "www", "mail", "ftp", "admin", "webmail", "api", "dev", "test", "staging",
    "cdn", "blog", "shop", "store", "app", "portal", "vpn", "remote", "ns1",
    "ns2", "mx", "smtp", "pop", "imap", "beta", "demo", "docs", "help",
    "support", "status", "static", "assets", "media", "img", "images", "video"
]

COMMON_SUBS_MEDIUM = COMMON_SUBS_SMALL + [
    "auth", "sso", "login", "signin", "signup", "register", "account", "my",
    "user", "users", "profile", "dashboard", "console", "manage", "management",
    "control", "cp", "cpanel", "whm", "plesk", "wp", "wordpress", "cms",
    "phpmyadmin", "mysql", "db", "database", "sql", "redis", "cache",
    "grafana", "kibana", "elastic", "prometheus", "jenkins", "ci", "cd",
    "build", "deploy", "gitlab", "git", "github", "svn", "jira", "confluence",
    "wiki", "kb", "knowledgebase", "internal", "intranet", "private", "secure",
    "ssl", "old", "new", "backup", "backups", "archive", "download", "downloads",
    "upload", "uploads", "files", "share", "shared", "cloud", "storage",
    "video", "videos", "audio", "music", "podcast", "stream", "streaming",
    "live", "chat", "im", "irc", "slack", "discord", "matrix", "forum",
    "community", "board", "news", "press", "media", "events", "calendar",
    "meet", "meeting", "conf", "conference", "webinar", "elearn", "learn",
    "learning", "training", "courses", "school", "university", "campus",
    "student", "students", "teacher", "faculty", "hr", "careers", "jobs",
    "sales", "marketing", "crm", "leads", "customer", "customers", "clients",
    "partners", "partner", "vendor", "vendors", "supplier", "suppliers",
    "billing", "pay", "payment", "payments", "invoice", "invoicing", "accounts",
    "finance", "reports", "reporting", "analytics", "stats", "metrics",
    "monitor", "monitoring", "watch", "log", "logs", "logger", "logging",
    "syslog", "elastic", "search", "elk", "logstash", "graylog", "sentry",
    "bugs", "issues", "tracker", "test1", "test2", "dev1", "dev2", "qa",
    "sandbox", "playground", "lab", "labs", "research", "beta1", "alpha",
    "preview", "next", "future", "prod", "production", "prd", "live",
    "www1", "www2", "www3", "web", "web1", "web2", "server", "srv", "host",
    "hosting", "vm", "docker", "k8s", "kubernetes", "swarm", "cluster",
    "node", "nodes", "worker", "workers", "master", "primary", "secondary"
]


def _resolve(name: str, timeout: float = 3.0) -> str:
    """Return first A record or empty string."""
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = timeout
        resolver.lifetime = timeout
        ans = resolver.resolve(name, "A")
        return str(ans[0])
    except dns.exception.DNSException:
        return ""


def _live_check(subdomain: str) -> dict:
    """Resolve and optionally probe HTTP."""
    ip = _resolve(subdomain)
    if not ip:
        return {"subdomain": subdomain, "resolves": False}
    result = {"subdomain": subdomain, "resolves": True, "ip": ip}
    # Try HTTP probe (fast, 4s max)
    for scheme in ("https", "http"):
        try:
            r = requests.head(f"{scheme}://{subdomain}", timeout=4, allow_redirects=False,
                              headers={"User-Agent": "DFI/1.0"})
            result["http"] = {"scheme": scheme, "status": r.status_code,
                              "server": r.headers.get("Server", "")}
            break
        except requests.RequestException:
            continue
    return result


def _query_crtsh(domain: str) -> set:
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "DFI/1.0"})
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError):
        return set()
    subs = set()
    for entry in data:
        for line in entry.get("name_value", "").split("\n"):
            line = line.strip().lower()
            if line and line.endswith(domain) and "*" not in line:
                subs.add(line)
    return subs


def run(target: str, mode: str = "basic", live_check: bool = False,
        bruteforce: bool = False) -> dict:
    """Subdomain enumeration.

    mode: 'basic' (crt.sh only) or 'advanced' (crt.sh + DNS bruteforce)
    live_check: verify each subdomain resolves and probe HTTP
    bruteforce: use DNS wordlist bruteforce (advanced mode enables this by default)
    """
    target = (target or "").strip().lower()
    if not target:
        return {"error": "Domain required."}
    target = target.replace("http://", "").replace("https://", "").split("/")[0]

    sources = {}

    # Source 1: crt.sh
    crt_subs = _query_crtsh(target)
    sources["crt.sh"] = len(crt_subs)
    all_subs = set(crt_subs)

    # Source 2: DNS bruteforce
    if mode == "advanced" or bruteforce:
        wordlist = COMMON_SUBS_MEDIUM if mode == "advanced" else COMMON_SUBS_SMALL
        brute_subs = set()
        with ThreadPoolExecutor(max_workers=30) as ex:
            candidates = [f"{w}.{target}" for w in wordlist]
            futures = {ex.submit(_resolve, c): c for c in candidates}
            for f in as_completed(futures):
                candidate = futures[f]
                ip = f.result()
                if ip:
                    brute_subs.add(candidate)
        sources["dns_brute"] = len(brute_subs)
        all_subs |= brute_subs

    sub_list = sorted(all_subs)

    # Live check
    live_results = None
    if live_check and sub_list:
        live_results = []
        with ThreadPoolExecutor(max_workers=25) as ex:
            for r in ex.map(_live_check, sub_list[:100]):  # cap at 100 for speed
                live_results.append(r)
        alive = [r for r in live_results if r["resolves"]]
    else:
        alive = None

    return {
        "target": target,
        "mode": mode,
        "sources": sources,
        "count": len(sub_list),
        "subdomains": sub_list,
        "live_check": live_results,
        "summary": f"Found {len(sub_list)} subdomain(s) from {len(sources)} source(s)."
                   + (f" {len(alive)} resolve." if alive is not None else "")
    }
