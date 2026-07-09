"""Directory / file bruteforce with a built-in wordlist."""
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

COMMON_PATHS = [
    "admin", "administrator", "login", "wp-admin", "wp-login.php",
    "phpmyadmin", "config", "config.php", "backup", "backups", "db",
    "database", "test", "dev", "staging", "api", "api/v1", "api/v2",
    "docs", "documentation", "swagger", "graphql", "graphiql",
    "robots.txt", "sitemap.xml", ".env", ".git", ".git/config", ".svn",
    ".htaccess", "server-status", "phpinfo.php", "info.php",
    "uploads", "upload", "images", "static", "assets", "public",
    "private", "hidden", "old", "new", "beta", "temp", "tmp",
    "user", "users", "profile", "account", "settings", "dashboard",
    "portal", "cms", "blog", "wiki", "forum", "shop", "cart",
    ".DS_Store", "readme.md", "README.md", "CHANGELOG.md", "LICENSE",
    "package.json", "composer.json", "web.config", "crossdomain.xml"
]

INTERESTING_CODES = {200, 201, 301, 302, 307, 401, 403}


def _check(base_url: str, path: str, timeout: float = 5.0):
    url = urljoin(base_url + "/", path)
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=False,
                          headers={"User-Agent": "DFI/1.0"})
        return {"path": path, "url": url, "status": r.status_code,
                "size": r.headers.get("Content-Length", "-")}
    except requests.RequestException:
        return None


def run(target: str, wordlist: list = None) -> dict:
    target = (target or "").strip().rstrip("/")
    if not target:
        return {"error": "URL required."}
    if not target.startswith(("http://", "https://")):
        target = "http://" + target

    paths = wordlist if wordlist else COMMON_PATHS
    found = []

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(_check, target, p) for p in paths]
        for future in as_completed(futures):
            result = future.result()
            if result and result["status"] in INTERESTING_CODES:
                found.append(result)

    found.sort(key=lambda x: (x["status"], x["path"]))

    return {
        "target": target,
        "paths_tested": len(paths),
        "found": found,
        "summary": f"Discovered {len(found)} interesting path(s) out of {len(paths)} tested."
    }
