"""Social media aggregator - generates search links + reuses username lookup."""
from backend.tools import username_lookup


def run(target: str) -> dict:
    q = (target or "").strip()
    if not q:
        return {"error": "Name or handle required."}

    # If input looks like a username (no spaces), also run username lookup
    if " " not in q and "@" not in q:
        uname_data = username_lookup.run(q)
    else:
        uname_data = None

    encoded = q.replace(" ", "+")
    search_urls = {
        "Twitter/X":    f"https://twitter.com/search?q={encoded}&f=user",
        "Facebook":     f"https://www.facebook.com/search/people/?q={encoded}",
        "LinkedIn":     f"https://www.linkedin.com/pub/dir/?firstAndLast={encoded}",
        "Instagram":    f"https://www.instagram.com/explore/tags/{encoded.replace('+','')}/",
        "Reddit":       f"https://www.reddit.com/search/?q={encoded}&type=user",
        "TikTok":       f"https://www.tiktok.com/search/user?q={encoded}",
        "YouTube":      f"https://www.youtube.com/results?search_query={encoded}&sp=EgIQAg%253D%253D",
        "Google":       f"https://www.google.com/search?q=%22{encoded}%22+profile+OR+bio",
        "PeekYou":      f"https://www.peekyou.com/{encoded}",
    }

    return {
        "target": q,
        "search_links": search_urls,
        "username_lookup": uname_data,
        "summary": f"Generated {len(search_urls)} social media search links."
                   + (f" Found on {len(uname_data.get('found_on', []))} platforms." if uname_data else "")
    }
