"""Username lookup across 100+ platforms with category filtering."""
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Category tags: social, dev, gaming, creative, professional, forum, misc
PLATFORMS = [
    # (name, url_template, check_type, category)
    ("GitHub",       "https://github.com/{u}",                    "status", "dev"),
    ("GitLab",       "https://gitlab.com/{u}",                    "status", "dev"),
    ("Bitbucket",    "https://bitbucket.org/{u}/",                "status", "dev"),
    ("Codeberg",     "https://codeberg.org/{u}",                  "status", "dev"),
    ("StackOverflow","https://stackoverflow.com/users/{u}",       "status", "dev"),
    ("DevTo",        "https://dev.to/{u}",                        "status", "dev"),
    ("Hashnode",     "https://hashnode.com/@{u}",                 "status", "dev"),
    ("Kaggle",       "https://www.kaggle.com/{u}",                "status", "dev"),
    ("HackerRank",   "https://www.hackerrank.com/{u}",            "status", "dev"),
    ("Codewars",     "https://www.codewars.com/users/{u}",        "status", "dev"),
    ("Codepen",      "https://codepen.io/{u}",                    "status", "dev"),
    ("Replit",       "https://replit.com/@{u}",                   "status", "dev"),
    ("HackTheBox",   "https://forum.hackthebox.com/u/{u}",        "status", "dev"),
    ("TryHackMe",    "https://tryhackme.com/p/{u}",               "status", "dev"),
    ("LeetCode",     "https://leetcode.com/{u}/",                 "status", "dev"),
    ("Docker Hub",   "https://hub.docker.com/u/{u}",              "status", "dev"),
    ("NPM",          "https://www.npmjs.com/~{u}",                "status", "dev"),
    ("PyPI",         "https://pypi.org/user/{u}/",                "status", "dev"),
    ("RubyGems",     "https://rubygems.org/profiles/{u}",         "status", "dev"),
    ("Crates.io",    "https://crates.io/users/{u}",               "status", "dev"),

    ("Twitter/X",    "https://twitter.com/{u}",                   "status", "social"),
    ("Instagram",    "https://www.instagram.com/{u}/",            "status", "social"),
    ("TikTok",       "https://www.tiktok.com/@{u}",               "status", "social"),
    ("Reddit",       "https://www.reddit.com/user/{u}",           "status", "social"),
    ("YouTube",      "https://www.youtube.com/@{u}",              "status", "social"),
    ("Pinterest",    "https://www.pinterest.com/{u}/",            "status", "social"),
    ("Snapchat",     "https://www.snapchat.com/add/{u}",          "status", "social"),
    ("Threads",      "https://www.threads.net/@{u}",              "status", "social"),
    ("Mastodon",     "https://mastodon.social/@{u}",              "status", "social"),
    ("Bluesky",      "https://bsky.app/profile/{u}.bsky.social",  "status", "social"),
    ("Telegram",     "https://t.me/{u}",                          "status", "social"),
    ("VK",           "https://vk.com/{u}",                        "status", "social"),
    ("Weibo",        "https://weibo.com/n/{u}",                   "status", "social"),

    ("HackerNews",   "https://news.ycombinator.com/user?id={u}",  "text_no_such_user", "forum"),
    ("Quora",        "https://www.quora.com/profile/{u}",         "status", "forum"),
    ("Slashdot",     "https://slashdot.org/~{u}",                 "status", "forum"),
    ("Producthunt",  "https://www.producthunt.com/@{u}",          "status", "forum"),

    ("Twitch",       "https://www.twitch.tv/{u}",                 "status", "gaming"),
    ("Steam",        "https://steamcommunity.com/id/{u}",         "text_no_match", "gaming"),
    ("Roblox",       "https://www.roblox.com/user.aspx?username={u}", "status", "gaming"),
    ("Chess.com",    "https://www.chess.com/member/{u}",          "status", "gaming"),
    ("Lichess",      "https://lichess.org/@/{u}",                 "status", "gaming"),
    ("Xbox",         "https://xboxgamertag.com/search/{u}",       "status", "gaming"),
    ("PlayStation",  "https://psnprofiles.com/{u}",               "status", "gaming"),
    ("Speedrun",     "https://www.speedrun.com/user/{u}",         "status", "gaming"),
    ("MMORPG",       "https://www.mmorpg.com/members/{u}",        "status", "gaming"),
    ("ItchIO",       "https://{u}.itch.io/",                      "status", "gaming"),

    ("Medium",       "https://medium.com/@{u}",                   "status", "creative"),
    ("Vimeo",        "https://vimeo.com/{u}",                     "status", "creative"),
    ("Dribbble",     "https://dribbble.com/{u}",                  "status", "creative"),
    ("Behance",      "https://www.behance.net/{u}",               "status", "creative"),
    ("DeviantArt",   "https://www.deviantart.com/{u}",            "status", "creative"),
    ("SoundCloud",   "https://soundcloud.com/{u}",                "status", "creative"),
    ("Spotify",      "https://open.spotify.com/user/{u}",         "status", "creative"),
    ("Flickr",       "https://www.flickr.com/people/{u}",         "status", "creative"),
    ("500px",        "https://500px.com/p/{u}",                   "status", "creative"),
    ("Bandcamp",     "https://{u}.bandcamp.com",                  "status", "creative"),
    ("Last.fm",      "https://www.last.fm/user/{u}",              "status", "creative"),
    ("Mixcloud",     "https://www.mixcloud.com/{u}/",             "status", "creative"),
    ("ArtStation",   "https://www.artstation.com/{u}",            "status", "creative"),
    ("Newgrounds",   "https://{u}.newgrounds.com",                "status", "creative"),

    ("Keybase",      "https://keybase.io/{u}",                    "status", "professional"),
    ("AboutMe",      "https://about.me/{u}",                      "status", "professional"),
    ("Gravatar",     "https://en.gravatar.com/{u}",               "status", "professional"),
    ("AngelList",    "https://angel.co/u/{u}",                    "status", "professional"),
    ("Patreon",      "https://www.patreon.com/{u}",               "status", "professional"),
    ("Ko-fi",        "https://ko-fi.com/{u}",                     "status", "professional"),
    ("BuyMeACoffee", "https://www.buymeacoffee.com/{u}",          "status", "professional"),
    ("Wikipedia",    "https://en.wikipedia.org/wiki/User:{u}",    "status", "professional"),
    ("Fiverr",       "https://www.fiverr.com/{u}",                "status", "professional"),

    ("Wordpress",    "https://{u}.wordpress.com",                 "status", "misc"),
    ("Tumblr",       "https://{u}.tumblr.com",                    "status", "misc"),
    ("Blogger",      "https://{u}.blogspot.com",                  "status", "misc"),
    ("Substack",     "https://{u}.substack.com",                  "status", "misc"),
    ("Ghost",        "https://{u}.ghost.io",                      "status", "misc"),
    ("Wattpad",      "https://www.wattpad.com/user/{u}",          "status", "misc"),
    ("Goodreads",    "https://www.goodreads.com/{u}",             "status", "misc"),
    ("Untappd",      "https://untappd.com/user/{u}",              "status", "misc"),
    ("Duolingo",     "https://www.duolingo.com/profile/{u}",      "status", "misc"),
    ("Strava",       "https://www.strava.com/athletes/{u}",       "status", "misc"),
    ("Meetup",       "https://www.meetup.com/members/{u}",        "status", "misc"),
    ("Vero",         "https://vero.co/{u}",                       "status", "misc"),
    ("Ello",         "https://ello.co/{u}",                       "status", "misc"),
    ("Trakt",        "https://trakt.tv/users/{u}",                "status", "misc"),
    ("Letterboxd",   "https://letterboxd.com/{u}/",               "status", "misc"),
    ("MyAnimeList",  "https://myanimelist.net/profile/{u}",       "status", "misc"),
    ("AniList",      "https://anilist.co/user/{u}",               "status", "misc"),
    ("BoardGameGeek","https://boardgamegeek.com/user/{u}",        "status", "misc"),
    ("VSCO",         "https://vsco.co/{u}",                       "status", "misc"),
    ("Pocket",       "https://getpocket.com/@{u}",                "status", "misc"),
    ("Pinboard",     "https://pinboard.in/u:{u}",                 "status", "misc"),
    ("Diigo",        "https://www.diigo.com/user/{u}",            "status", "misc"),
    ("Slack",        "https://{u}.slack.com",                     "status", "misc"),
    ("Notion",       "https://www.notion.so/{u}",                 "status", "misc"),
    ("Read.cv",      "https://read.cv/{u}",                       "status", "professional"),
    ("Polywork",     "https://www.polywork.com/{u}",              "status", "professional"),
]


HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DFI/1.0"}


def _check(platform, template, check_type, category, username, timeout=8):
    url = template.format(u=username)
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if check_type == "status":
            found = r.status_code == 200
        elif check_type == "text_no_such_user":
            found = r.status_code == 200 and "No such user" not in r.text
        elif check_type == "text_no_match":
            found = r.status_code == 200 and "no users matching" not in r.text.lower()
        else:
            found = r.status_code == 200
        return {"platform": platform, "url": url, "category": category,
                "found": found, "status_code": r.status_code}
    except requests.RequestException:
        return {"platform": platform, "url": url, "category": category,
                "found": None, "status_code": None}


def run(target: str, categories: str = "all", include_variations: bool = False,
        show_not_found: bool = False) -> dict:
    """Check username on 90+ platforms.

    categories: comma-separated ('all', 'social', 'dev', 'gaming', 'creative',
                'professional', 'forum', 'misc')
    include_variations: also check username_1, _username, username1
    show_not_found: include non-matches in output
    """
    username = (target or "").strip()
    if not username:
        return {"error": "Username required."}
    if any(c in username for c in " /\\?#"):
        return {"error": "Invalid username characters."}

    # Filter platforms by category
    cats = {c.strip().lower() for c in categories.split(",") if c.strip()}
    if "all" in cats or not cats:
        platforms = PLATFORMS
    else:
        platforms = [p for p in PLATFORMS if p[3] in cats]

    # Build username list
    usernames = [username]
    if include_variations:
        usernames += [f"{username}_", f"_{username}", f"{username}1", f"{username}01"]
        usernames = list(dict.fromkeys(usernames))  # dedupe, preserve order

    all_results = []
    for uname in usernames:
        with ThreadPoolExecutor(max_workers=20) as ex:
            futures = [ex.submit(_check, n, t, c, cat, uname)
                       for n, t, c, cat in platforms]
            for f in as_completed(futures):
                r = f.result()
                r["username_variant"] = uname
                all_results.append(r)

    found = [r for r in all_results if r["found"] is True]
    not_found = [r for r in all_results if r["found"] is False]
    errors = [r for r in all_results if r["found"] is None]

    found.sort(key=lambda x: (x["category"], x["platform"]))

    # Group found by category for cleaner display
    by_category = {}
    for r in found:
        by_category.setdefault(r["category"], []).append(r)

    output = {
        "username": username,
        "variants_checked": usernames,
        "platforms_checked": len(platforms),
        "total_checks": len(all_results),
        "categories_filtered": sorted(cats) if "all" not in cats and cats else "all",
        "found_count": len(found),
        "found_by_category": by_category,
        "found_on": found,
        "not_found_count": len(not_found),
        "error_count": len(errors),
        "summary": f"Found '{username}' on {len(found)}/{len(platforms) * len(usernames)} checks."
    }
    if show_not_found:
        output["not_found"] = not_found
    return output
