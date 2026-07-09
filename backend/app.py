"""Digital Footprint Investigator - Flask backend.

Run:  python -m backend.app
Then open: http://localhost:5000
"""
import traceback
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from backend.tools import (
    port_scan, dns_enum, subdomain_enum, whois_lookup, dir_brute,
    web_crawler, ssl_scan, banner_grab,
    authentication, username_lookup, email_investigation,
    domain_investigation, ip_investigation, phone_investigation,
    metadata_extraction, website_analysis,
    social_media, breach_check, reverse_image, google_dorking,
    public_records, dark_web,
)

ROOT = Path(__file__).parent.parent

app = Flask(__name__, static_folder=str(ROOT), static_url_path="")
CORS(app)


TOOLS = {
    # Active
    "port-scan":            port_scan.run,
    "dns-enum":             dns_enum.run,
    "subdomain-enum":       subdomain_enum.run,
    "whois":                whois_lookup.run,
    "dir-brute":            dir_brute.run,
    "web-crawler":          web_crawler.run,
    "ssl-scan":             ssl_scan.run,
    "banner-grab":          banner_grab.run,
    # Passive
    "authentication":       authentication.run,
    "username-lookup":      username_lookup.run,
    "email-investigation":  email_investigation.run,
    "domain-investigation": domain_investigation.run,
    "ip-investigation":     ip_investigation.run,
    "phone-investigation":  phone_investigation.run,
    "metadata-extraction":  metadata_extraction.run,
    "website-analysis":     website_analysis.run,
    "social-media":         social_media.run,
    "breach-check":         breach_check.run,
    "reverse-image":        reverse_image.run,
    "google-dorking":       google_dorking.run,
    "public-records":       public_records.run,
    "dark-web":             dark_web.run,
}


# ---------- Static: serve the frontend ----------
@app.route("/")
def index():
    return send_from_directory(str(ROOT), "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(str(ROOT), filename)


# ---------- Health check ----------
@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "tools_available": list(TOOLS.keys())})


# ---------- Main tool runner ----------
@app.route("/api/run/<tool_id>", methods=["POST"])
def run_tool(tool_id):
    if tool_id not in TOOLS:
        return jsonify({"error": f"Unknown tool: {tool_id}"}), 404

    # Metadata extraction supports file upload with optional mode field
    if tool_id == "metadata-extraction" and request.files:
        f = request.files.get("file")
        if f:
            mode = request.form.get("mode", "basic")
            try:
                result = metadata_extraction.run(
                    target="", file_bytes=f.read(), filename=f.filename, mode=mode
                )
                return jsonify(result)
            except Exception:
                return jsonify({"error": traceback.format_exc()}), 500

    data = request.get_json(silent=True) or {}
    target = data.get("target", "")
    options = data.get("options", {}) or {}

    # Filter out empty/None values so tool defaults kick in
    clean_options = {k: v for k, v in options.items()
                     if v is not None and v != ""}

    try:
        if clean_options:
            result = TOOLS[tool_id](target, **clean_options)
        else:
            result = TOOLS[tool_id](target)
        return jsonify(result)
    except TypeError as e:
        # Tool doesn't accept some kwargs - try without them
        try:
            result = TOOLS[tool_id](target)
            return jsonify(result)
        except Exception:
            return jsonify({"error": f"Options mismatch: {e}\n" + traceback.format_exc()}), 500
    except Exception:
        return jsonify({"error": traceback.format_exc()}), 500


# ---------- Authentication endpoints ----------
@app.route("/api/auth/status")
def auth_status():
    return jsonify(authentication.get_status())


@app.route("/api/auth/update", methods=["POST"])
def auth_update():
    data = request.get_json(silent=True) or {}
    service = data.get("service", "")
    key = data.get("key", "")
    return jsonify(authentication.update(service, key))


if __name__ == "__main__":
    print("=" * 60)
    print("  Digital Footprint Investigator")
    print("  Starting on http://localhost:5000")
    print(f"  Tools loaded: {len(TOOLS)}")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5000, debug=False)
