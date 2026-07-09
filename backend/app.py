"""Digital Footprint Investigator - Flask backend.

Run:  python -m backend.app
Then open: http://localhost:5000
"""
import hashlib
import io
import traceback
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS

from backend import db, correlation, report_generator
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
    "port-scan":            (port_scan.run,             "Port Scanning",         "active"),
    "dns-enum":             (dns_enum.run,              "DNS Enumeration",       "active"),
    "subdomain-enum":       (subdomain_enum.run,        "Subdomain Enumeration", "active"),
    "whois":                (whois_lookup.run,          "WHOIS Lookup",          "active"),
    "dir-brute":            (dir_brute.run,             "Directory Bruteforce",  "active"),
    "web-crawler":          (web_crawler.run,           "Web Crawler",           "active"),
    "ssl-scan":             (ssl_scan.run,              "SSL / TLS Scanner",     "active"),
    "banner-grab":          (banner_grab.run,           "Banner Grabbing",       "active"),
    "authentication":       (authentication.run,        "Authentication",        "passive"),
    "username-lookup":      (username_lookup.run,       "Username Lookup",       "passive"),
    "email-investigation":  (email_investigation.run,   "Email Investigation",   "passive"),
    "domain-investigation": (domain_investigation.run,  "Domain Investigation",  "passive"),
    "ip-investigation":     (ip_investigation.run,      "IP Investigation",      "passive"),
    "phone-investigation":  (phone_investigation.run,   "Phone Investigation",   "passive"),
    "metadata-extraction":  (metadata_extraction.run,   "Metadata Extraction",   "passive"),
    "website-analysis":     (website_analysis.run,      "Website Analysis",      "passive"),
    "social-media":         (social_media.run,          "Social Media Search",   "passive"),
    "breach-check":         (breach_check.run,          "Data Breach Check",     "passive"),
    "reverse-image":        (reverse_image.run,         "Reverse Image Search",  "passive"),
    "google-dorking":       (google_dorking.run,        "Google Dorking",        "passive"),
    "public-records":       (public_records.run,        "Public Records",        "passive"),
    "dark-web":             (dark_web.run,              "Dark Web Monitor",      "passive"),
}

# Tools where we do NOT auto-save to a case (no meaningful investigation data)
NO_CASE_TOOLS = {"authentication"}


# ============ INIT ============

db.init_db()


# ============ STATIC ============

@app.route("/")
def index():
    return send_from_directory(str(ROOT), "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(str(ROOT), filename)


# ============ HEALTH ============

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "tools_available": list(TOOLS.keys())})


# ============ TOOL RUNNER (case-aware) ============

def _resolve_case(case_id, target, tool_id, tool_name) -> int:
    """Return an existing case_id or create a new one for this run."""
    if case_id:
        try:
            case_id = int(case_id)
            if db.get_case(case_id):
                return case_id
        except (ValueError, TypeError):
            pass
    # Auto-create
    display_target = target or "(no target)"
    case_name = f"{display_target}"[:80]
    new_case = db.create_case(name=case_name, primary_target=target or "",
                              description=f"Auto-created from {tool_name}")
    return new_case["id"]


@app.route("/api/run/<tool_id>", methods=["POST"])
def run_tool(tool_id):
    if tool_id not in TOOLS:
        return jsonify({"error": f"Unknown tool: {tool_id}"}), 404

    tool_fn, tool_name, tool_type = TOOLS[tool_id]

    # --- Parse inputs (file upload OR JSON body) ---
    case_id = None
    target = ""
    options = {}
    file_bytes = None
    file_name = None

    if request.files:
        f = request.files.get("file")
        if f:
            file_bytes = f.read()
            file_name = f.filename
        target = request.form.get("target", "") or (f"[uploaded: {file_name}]" if file_name else "")
        case_id = request.form.get("case_id") or None
        mode = request.form.get("mode")
        if mode:
            options["mode"] = mode
    else:
        data = request.get_json(silent=True) or {}
        target = (data.get("target") or "").strip()
        options = data.get("options") or {}
        case_id = data.get("case_id")

    # Filter empty options so tool defaults apply
    clean_options = {k: v for k, v in options.items()
                     if v is not None and v != ""}

    # --- Run the tool ---
    result = None
    error = None
    status = "success"
    try:
        if tool_id == "metadata-extraction" and file_bytes is not None:
            result = metadata_extraction.run(
                target="", file_bytes=file_bytes, filename=file_name,
                mode=clean_options.get("mode", "basic"),
            )
        elif clean_options:
            try:
                result = tool_fn(target, **clean_options)
            except TypeError:
                # Tool doesn't accept some kwargs — try without them
                result = tool_fn(target)
        else:
            result = tool_fn(target)

        if isinstance(result, dict) and result.get("error"):
            status = "error"
            error = result.get("error")
    except Exception:
        status = "error"
        error = traceback.format_exc()
        result = {"error": error}

    # --- Persist to case (skip meta tools) ---
    saved = None
    if tool_id not in NO_CASE_TOOLS:
        try:
            resolved_case_id = _resolve_case(case_id, target, tool_id, tool_name)
            result_id = db.save_result(
                case_id=resolved_case_id, tool_id=tool_id, tool_name=tool_name,
                tool_type=tool_type, target=target or (file_name or ""),
                options=clean_options, status=status, result=result if status == "success" else None,
                error=error,
            )
            # Extract entities (only for successful runs)
            if status == "success":
                ents = correlation.extract_entities(tool_id, target, result)
                db.add_entities(resolved_case_id, ents, tool_id, result_id)

            # Build suggestions from current case entities
            all_ents = db.get_entities(resolved_case_id)
            executed = {(r["tool_id"], r["target"])
                        for r in db.get_case(resolved_case_id)["results"]}
            suggestions = correlation.suggest_next(all_ents, executed_tools=executed)

            saved = {
                "case_id": resolved_case_id,
                "result_id": result_id,
                "extracted_entities": len(ents) if status == "success" else 0,
                "suggestions": suggestions[:10],
            }
        except Exception:
            # Never break the API just because DB failed
            saved = {"error": traceback.format_exc()}

    # --- Response ---
    if status == "error":
        payload = result if isinstance(result, dict) else {"error": str(result)}
        payload["_meta"] = saved
        return jsonify(payload), 200  # 200 with error field is the convention we already use
    else:
        result = dict(result) if isinstance(result, dict) else {"result": result}
        result["_meta"] = saved
        return jsonify(result)


# ============ CASE MANAGEMENT ============

@app.route("/api/cases", methods=["GET"])
def cases_list():
    return jsonify({"cases": db.list_cases()})


@app.route("/api/cases", methods=["POST"])
def cases_create():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    primary_target = data.get("primary_target", "").strip()
    description = data.get("description", "").strip()
    if not name:
        name = primary_target or f"Case {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    case = db.create_case(name, primary_target, description)
    return jsonify(case), 201


@app.route("/api/cases/<int:case_id>", methods=["GET"])
def cases_get(case_id):
    case = db.get_case(case_id)
    if not case:
        return jsonify({"error": "Case not found"}), 404
    all_ents = db.get_entities(case_id)
    executed = {(r["tool_id"], r["target"]) for r in case["results"]}
    case["suggestions"] = correlation.suggest_next(all_ents, executed_tools=executed)
    return jsonify(case)


@app.route("/api/cases/<int:case_id>", methods=["PATCH"])
def cases_update(case_id):
    data = request.get_json(silent=True) or {}
    updated = db.rename_case(case_id,
                              name=data.get("name"),
                              description=data.get("description"))
    if not updated:
        return jsonify({"error": "Case not found"}), 404
    return jsonify(updated)


@app.route("/api/cases/<int:case_id>", methods=["DELETE"])
def cases_delete(case_id):
    if not db.delete_case(case_id):
        return jsonify({"error": "Case not found"}), 404
    return jsonify({"deleted": True})


@app.route("/api/cases/<int:case_id>/suggestions", methods=["GET"])
def cases_suggestions(case_id):
    case = db.get_case(case_id)
    if not case:
        return jsonify({"error": "Case not found"}), 404
    all_ents = db.get_entities(case_id)
    executed = {(r["tool_id"], r["target"]) for r in case["results"]}
    return jsonify({"suggestions": correlation.suggest_next(all_ents, executed_tools=executed)})


@app.route("/api/cases/<int:case_id>/report.pdf", methods=["GET"])
def cases_report(case_id):
    case = db.get_case(case_id)
    if not case:
        return jsonify({"error": "Case not found"}), 404
    investigator = request.args.get("investigator", "DFI Investigator")
    try:
        pdf_bytes = report_generator.build_report(case, investigator=investigator)
    except Exception:
        return jsonify({"error": traceback.format_exc()}), 500
    sha = hashlib.sha256(pdf_bytes).hexdigest()
    safe_name = "".join(c if c.isalnum() or c in "-_." else "_"
                        for c in (case.get("name") or "case"))[:50]
    filename = f"dfi-report-{case_id}-{safe_name}.pdf"
    resp = send_file(io.BytesIO(pdf_bytes), mimetype="application/pdf",
                      as_attachment=True, download_name=filename)
    resp.headers["X-Report-SHA256"] = sha
    resp.headers["Access-Control-Expose-Headers"] = "X-Report-SHA256"
    return resp


@app.route("/api/results/<int:result_id>", methods=["DELETE"])
def results_delete(result_id):
    if not db.delete_result(result_id):
        return jsonify({"error": "Result not found"}), 404
    return jsonify({"deleted": True})


@app.route("/api/entities/search", methods=["GET"])
def entities_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"results": []})
    return jsonify({"results": db.search_entities(q, limit=30)})


# ============ AUTHENTICATION ============

@app.route("/api/auth/status")
def auth_status():
    return jsonify(authentication.get_status())


@app.route("/api/auth/update", methods=["POST"])
def auth_update():
    data = request.get_json(silent=True) or {}
    return jsonify(authentication.update(data.get("service", ""), data.get("key", "")))


# ============ MAIN ============

if __name__ == "__main__":
    print("=" * 60)
    print("  Digital Footprint Investigator")
    print("  Starting on http://localhost:5000")
    print(f"  Tools loaded: {len(TOOLS)}")
    print(f"  Database: {db.DB_PATH}")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5000, debug=False)
