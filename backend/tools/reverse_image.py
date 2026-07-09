"""Reverse image search - generates search URLs for major engines."""
from urllib.parse import quote


def run(target: str) -> dict:
    img_url = (target or "").strip()
    if not img_url:
        return {"error": "Image URL required."}
    if not img_url.startswith(("http://", "https://")):
        return {"error": "URL must start with http:// or https://"}

    encoded = quote(img_url, safe="")
    engines = {
        "Google Images":   f"https://www.google.com/searchbyimage?image_url={encoded}",
        "Google Lens":     f"https://lens.google.com/uploadbyurl?url={encoded}",
        "Yandex Images":   f"https://yandex.com/images/search?rpt=imageview&url={encoded}",
        "TinEye":          f"https://tineye.com/search?url={encoded}",
        "Bing Visual":     f"https://www.bing.com/images/search?q=imgurl:{encoded}&view=detailv2&iss=sbi",
        "Baidu":           f"https://graph.baidu.com/details?isfromtusoupc=1&tn=pc&carousel=0&image={encoded}",
    }

    return {
        "target": img_url,
        "search_engines": engines,
        "note": "Open the links in your browser. Programmatic reverse image search requires paid APIs (TinEye, Google Cloud Vision).",
        "summary": f"Generated reverse image search URLs for {len(engines)} engines."
    }
