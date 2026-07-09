"""Directory bruteforce - configurable wordlist size and file extensions."""
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

WORDLIST_SMALL = [
    "admin", "administrator", "login", "wp-admin", "wp-login.php",
    "phpmyadmin", "config", "backup", "test", "dev", "api", "docs",
    "robots.txt", "sitemap.xml", ".env", ".git/config", ".htaccess",
    "server-status", "phpinfo.php", "uploads", "images", "static",
    "dashboard", "portal", "cms", "readme.md", "package.json"
]

WORDLIST_MEDIUM = WORDLIST_SMALL + [
    "administrator", "wp-login", "wp-content", "wp-includes", "config.php",
    "config.inc.php", "database.php", "settings.php", "wp-config.php",
    "backups", "db", "database", "staging", "beta", "alpha", "old", "new",
    "temp", "tmp", "cache", "logs", "log", "error.log", "access.log",
    "api/v1", "api/v2", "api/v3", "api/docs", "swagger", "swagger.json",
    "swagger.yaml", "graphql", "graphiql", "openapi.json", "redoc",
    "documentation", "docs/api", "help", "faq", "support", "contact",
    "index.php", "index.html", "index.jsp", "index.asp", "default.asp",
    "login.php", "signin", "signup", "register", "logout",
    "user", "users", "profile", "account", "accounts", "settings",
    "hidden", "private", "secret", "internal", "intranet",
    ".DS_Store", ".svn", ".git", ".git/HEAD", ".gitignore", ".hg",
    ".bak", ".old", ".backup", ".swp", "web.config", "crossdomain.xml",
    "clientaccesspolicy.xml", "composer.json", "composer.lock",
    "Gemfile", "Gemfile.lock", "requirements.txt", "yarn.lock",
    "package-lock.json", "manifest.json", "app.js", "main.js",
    "server-info", "status", "health", "healthcheck", "ping", "version",
    "info.php", "test.php", "phptest.php", "shell.php", "cmd.php",
    "console", "admin.php", "admin/login", "administrator/index.php",
    "manager", "manage", "control", "cp", "cpanel", "webmail",
    "backup.zip", "backup.tar", "backup.tar.gz", "backup.sql", "db.sql",
    "dump.sql", "database.sql", "test.zip", "site.zip", "www.zip"
]

# Building the large list dynamically (would be too long to hardcode)
WORDLIST_LARGE = WORDLIST_MEDIUM + [
    f"{p}" for p in [
        "actuator", "actuator/health", "actuator/env", "actuator/mappings",
        "actuator/beans", "actuator/heapdump", "actuator/trace", "actuator/loggers",
        ".well-known/security.txt", ".well-known/change-password", ".well-known/openid-configuration",
        ".well-known/webfinger", ".well-known/apple-app-site-association",
        "assets", "public", "resources", "storage", "vendor",
        "node_modules", "vendor/composer", "public_html", "www", "html",
        "cgi-bin", "cgi", "scripts", "includes", "inc", "lib", "libs",
        "download", "downloads", "upload", "files", "documents", "media",
        "css", "js", "javascript", "fonts", "audio", "video", "gallery",
        "forum", "community", "blog", "wiki", "news",
        "member", "members", "customer", "customers", "client", "clients",
        "shop", "store", "cart", "checkout", "order", "orders",
        "search", "sitemap", "sitemap.txt", "feed", "feed.xml", "rss", "atom.xml",
        "trackback", "wp-json", "wp-cron.php", "xmlrpc.php",
        "phpMyAdmin", "pma", "adminer", "adminer.php", "myadmin",
        "shell.php", "c99.php", "r57.php", "webshell.php", "backdoor.php",
        "config.old", "config.bak", "config.php.bak", "wp-config.php.bak",
        "db.php", "connection.php", "connect.php", "conn.php",
        "install", "install.php", "setup.php", "installer.php",
        "upgrade.php", "update.php", "maintenance.html",
        "reports", "report", "export", "export.php", "excel", "csv",
        "print", "printable", "preview", "draft", "drafts",
        "monitoring", "monitor", "stats", "statistics", "analytics",
        "metrics", "prometheus", "grafana", "kibana", "elastic",
        "jenkins", "gitlab", "github", "bitbucket", "jira", "confluence",
        "sonarqube", "sonar", "nexus", "artifactory", "harbor",
        "kubernetes", "kubelet", "docker", "consul", "vault", "nomad"
    ]
]


def _check(base_url: str, path: str, timeout: float, follow_redirects: bool, extensions: list):
    """Try path with each extension appended (or no extension)."""
    results = []
    variants = [path] + [f"{path}.{ext}" for ext in extensions]
    for variant in variants:
        url = urljoin(base_url + "/", variant)
        try:
            r = requests.head(url, timeout=timeout, allow_redirects=follow_redirects,
                              headers={"User-Agent": "Mozilla/5.0 DFI/1.0"})
            if r.status_code in (200, 201, 301, 302, 307, 401, 403):
                results.append({
                    "path": variant, "url": url, "status": r.status_code,
                    "size": r.headers.get("Content-Length", "-"),
                    "server": r.headers.get("Server", "")
                })
        except requests.RequestException:
            pass
    return results


def run(target: str, wordlist_size: str = "small", extensions: str = "",
        follow_redirects: bool = False, timeout: float = 5.0) -> dict:
    """Directory bruteforce.

    wordlist_size: 'small' (~25), 'medium' (~130), 'large' (~200)
    extensions: comma-separated extensions to append (e.g. 'php,html,txt')
    follow_redirects: follow HTTP 3xx redirects
    """
    target = (target or "").strip().rstrip("/")
    if not target:
        return {"error": "URL required."}
    if not target.startswith(("http://", "https://")):
        target = "http://" + target

    wordlists = {"small": WORDLIST_SMALL, "medium": WORDLIST_MEDIUM, "large": WORDLIST_LARGE}
    wordlist = wordlists.get(wordlist_size, WORDLIST_SMALL)
    ext_list = [e.strip().lstrip(".") for e in extensions.split(",") if e.strip()]

    found = []
    with ThreadPoolExecutor(max_workers=25) as ex:
        futures = [ex.submit(_check, target, p, timeout, follow_redirects, ext_list) for p in wordlist]
        for f in as_completed(futures):
            found.extend(f.result())

    # Deduplicate by URL
    seen = set()
    deduped = []
    for r in found:
        if r["url"] not in seen:
            seen.add(r["url"])
            deduped.append(r)

    deduped.sort(key=lambda x: (x["status"], x["path"]))
    total_tested = len(wordlist) * (1 + len(ext_list))

    return {
        "target": target,
        "wordlist_size": wordlist_size,
        "wordlist_count": len(wordlist),
        "extensions": ext_list,
        "paths_tested": total_tested,
        "found": deduped,
        "summary": f"Discovered {len(deduped)} path(s) out of {total_tested} tested "
                   f"({wordlist_size} wordlist)."
    }
