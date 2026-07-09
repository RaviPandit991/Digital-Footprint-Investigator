"""Username lookup - check username presence on 40+ platforms via HTTP status."""
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Platforms: (name, url_template, expected_error_indicator)
# error_type: 'status' = 404 means not found, 'text' = specific text means not found
PLATFORMS = [
    ("GitHub",       "https://github.com/{u}",                    "status"),
    ("Twitter/X",    "https://twitter.com/{u}",                   "status"),
    ("Instagram",    "https://www.instagram.com/{u}/",            "status"),
    ("Reddit",       "https://www.reddit.com/user/{u}",           "status"),
    ("YouTube",      "https://www.youtube.com/@{u}",              "status"),
    ("TikTok",       "https://www.tiktok.com/@{u}",               "status"),
    ("Pinterest",    "https://www.pinterest.com/{u}/",            "status"),
    ("Medium",       "https://medium.com/@{u}",                   "status"),
    ("DevTo",        "https://dev.to/{u}",                        "status"),
    ("HackerNews",   "https://news.ycombinator.com/user?id={u}",  "text_no_such_user"),
    ("StackOverflow","https://stackoverflow.com/users/{u}",       "status"),
    ("Kaggle",       "https://www.kaggle.com/{u}",                "status"),
    ("GitLab",       "https://gitlab.com/{u}",                    "status"),
    ("Bitbucket",    "https://bitbucket.org/{u}/",                "status"),
    ("Vimeo",        "https://vimeo.com/{u}",                     "status"),
    ("Dribbble",     "https://dribbble.com/{u}",                  "status"),
    ("Behance",      "https://www.behance.net/{u}",               "status"),
    ("SoundCloud",   "https://soundcloud.com/{u}",                "status"),
    ("Spotify",      "https://open.spotify.com/user/{u}",         "status"),
    ("Twitch",       "https://www.twitch.tv/{u}",                 "status"),
    ("Flickr",       "https://www.flickr.com/people/{u}",         "status"),
    ("Roblox",       "https://www.roblox.com/user.aspx?username={u}", "status"),
    ("Steam",        "https://steamcommunity.com/id/{u}",         "text_no_match"),
    ("Chess.com",    "https://www.chess.com/member/{u}",          "status"),
    ("Lichess",      "https://lichess.org/@/{u}",                 "status"),
    ("Keybase",      "https://keybase.io/{u}",                    "status"),
    ("AboutMe",      "https://about.me/{u}",                      "status"),
    ("Gravatar",     "https://en.gravatar.com/{u}",               "status"),
    ("Wordpress",    "https://{u}.wordpress.com",                 "status"),
    ("Tumblr",       "https://{u}.tumblr.com",                    "status"),
    ("Blogger",      "https://{u}.blogspot.com",                  "status"),
    ("HackTheBox",   "https://forum.hackthebox.com/u/{u}",        "status"),
    ("TryHackMe",    "https://tryhackme.com/p/{u}",               "status"),
    ("Codewars",     "https://www.codewars.com/users/{u}",        "status"),
    ("Codepen",      "https://codepen.io/{u}",                    "status"),
    ("Replit",       "https://replit.com/@{u}",                   "status"),
    ("Producthunt",  "https://www.producthunt.com/@{u}",          "status"),
    ("Patreon",      "https://www.patreon.com/{u}",               "status"),
    ("Ko-fi",        "https://ko-fi.com/{u}",                     "status"),
    ("Wikipedia",    "https://en.wikipedia.org/wiki/User:{u}",    "status"),
]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; DFI/1.0)"}


def _check(platform, template, error_type, username, timeout=6):
    url = template.format(u=username)
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if error_type == "status":
            found = r.status_code == 200
        elif error_type == "text_no_such_user":
            found = r.status_code == 200 and "No such user" not in r.text
        elif error_type == "text_no_match":
            found = r.status_code == 200 and "no users matching" not in r.text.lower()
        else:
            found = r.status_code == 200
        return {"platform": platform, "url": url, "found": found, "status_code": r.status_code}
    except requests.RequestException:
        return {"platform": platform, "url": url, "found": None, "status_code": None}


def run(target: str) -> dict:
    username = (target or "").strip()
    if not username:
        return {"error": "Username required."}
    if any(c in username for c in " /\\?#"):
        return {"error": "Invalid username characters."}

    results = []
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(_check, name, tmpl, etype, username)
                   for name, tmpl, etype in PLATFORMS]
        for future in as_completed(futures):
            results.append(future.result())

    found = [r for r in results if r["found"] is True]
    not_found = [r for r in results if r["found"] is False]
    errors = [r for r in results if r["found"] is None]

    found.sort(key=lambda x: x["platform"])
    return {
        "username": username,
        "platforms_checked": len(PLATFORMS),
        "found_on": found,
        "not_found_count": len(not_found),
        "error_count": len(errors),
        "summary": f"Found '{username}' on {len(found)}/{len(PLATFORMS)} platforms."
    }
