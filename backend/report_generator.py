"""PDF report generation using reportlab."""
import hashlib
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    KeepTogether, HRFlowable, ListFlowable, ListItem,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

# ============ COLORS ============
BRAND_PRIMARY = colors.HexColor("#0891b2")
BRAND_SECONDARY = colors.HexColor("#a855f7")
INK_DARK = colors.HexColor("#1e293b")
INK_MEDIUM = colors.HexColor("#475569")
INK_LIGHT = colors.HexColor("#94a3b8")
BG_TABLE_HEADER = colors.HexColor("#f1f4f9")
BG_TABLE_ALT = colors.HexColor("#f9fafc")
BORDER = colors.HexColor("#e2e8f0")

SUCCESS = colors.HexColor("#059669")
WARNING = colors.HexColor("#d97706")
DANGER = colors.HexColor("#dc2626")


def _styles():
    ss = getSampleStyleSheet()

    ss.add(ParagraphStyle(name="CoverTitle", fontSize=36, leading=42,
                          textColor=BRAND_PRIMARY, alignment=TA_CENTER,
                          spaceAfter=20, fontName="Helvetica-Bold"))
    ss.add(ParagraphStyle(name="CoverSubtitle", fontSize=14, leading=20,
                          textColor=INK_MEDIUM, alignment=TA_CENTER,
                          spaceAfter=10))
    ss.add(ParagraphStyle(name="CoverMeta", fontSize=11, leading=18,
                          textColor=INK_MEDIUM, alignment=TA_CENTER))
    ss.add(ParagraphStyle(name="SectionH1", fontSize=22, leading=28,
                          textColor=BRAND_PRIMARY, spaceBefore=24, spaceAfter=12,
                          fontName="Helvetica-Bold"))
    ss.add(ParagraphStyle(name="SectionH2", fontSize=15, leading=22,
                          textColor=INK_DARK, spaceBefore=16, spaceAfter=8,
                          fontName="Helvetica-Bold"))
    ss.add(ParagraphStyle(name="SectionH3", fontSize=12, leading=18,
                          textColor=BRAND_PRIMARY, spaceBefore=10, spaceAfter=6,
                          fontName="Helvetica-Bold"))
    ss.add(ParagraphStyle(name="Body", fontSize=10, leading=15,
                          textColor=INK_DARK, alignment=TA_JUSTIFY,
                          spaceAfter=6))
    ss.add(ParagraphStyle(name="BodyMuted", fontSize=9, leading=13,
                          textColor=INK_MEDIUM))
    ss.add(ParagraphStyle(name="Small", fontSize=8, leading=11,
                          textColor=INK_LIGHT))
    ss.add(ParagraphStyle(name="Mono", fontSize=8, leading=11,
                          textColor=INK_DARK, fontName="Courier"))
    ss.add(ParagraphStyle(name="Summary", fontSize=11, leading=16,
                          textColor=INK_DARK, leftIndent=12, rightIndent=12,
                          spaceBefore=8, spaceAfter=8,
                          borderColor=BRAND_PRIMARY, borderWidth=0,
                          borderPadding=10, backColor=BG_TABLE_HEADER))
    return ss


def _draw_header_footer(canvas, doc):
    """Draw page header and footer on every non-cover page."""
    if doc.page == 1:
        return
    canvas.saveState()
    # Header line
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, A4[1] - 0.6 * inch,
                A4[0] - doc.rightMargin, A4[1] - 0.6 * inch)
    canvas.setFillColor(INK_LIGHT)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(doc.leftMargin, A4[1] - 0.5 * inch,
                       "Digital Footprint Investigator Report")
    canvas.drawRightString(A4[0] - doc.rightMargin, A4[1] - 0.5 * inch,
                            datetime.utcnow().strftime("%Y-%m-%d"))
    # Footer
    canvas.line(doc.leftMargin, 0.6 * inch,
                A4[0] - doc.rightMargin, 0.6 * inch)
    canvas.drawString(doc.leftMargin, 0.4 * inch, "CONFIDENTIAL")
    canvas.drawCentredString(A4[0] / 2, 0.4 * inch, f"Page {doc.page}")
    canvas.drawRightString(A4[0] - doc.rightMargin, 0.4 * inch,
                            "For authorized use only")
    canvas.restoreState()


def _fmt(v, max_len=120):
    """Format any value for display in the PDF, escaping HTML."""
    if v is None:
        return "-"
    if isinstance(v, bool):
        return "Yes" if v else "No"
    if isinstance(v, (list, tuple)):
        return ", ".join(_fmt(x, 60) for x in v[:12]) + (f" (+{len(v)-12} more)" if len(v) > 12 else "")
    if isinstance(v, dict):
        pairs = [f"{k}: {_fmt(val, 30)}" for k, val in list(v.items())[:10]]
        return "; ".join(pairs)
    s = str(v)
    # Escape HTML characters that break reportlab
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    if len(s) > max_len:
        s = s[:max_len] + "..."
    return s


def _kv_table(rows, styles):
    """Build a two-column key/value table."""
    data = [[Paragraph(f"<b>{_fmt(k, 40)}</b>", styles["BodyMuted"]),
             Paragraph(_fmt(v, 200), styles["Body"])] for k, v in rows if v is not None]
    if not data:
        return Paragraph("<i>No data</i>", styles["BodyMuted"])
    t = Table(data, colWidths=[1.7 * inch, 4.3 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), BG_TABLE_HEADER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.4, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def _grid_table(headers, rows, styles, col_widths=None):
    """Build a general grid table with header row."""
    if not rows:
        return Paragraph("<i>No entries</i>", styles["BodyMuted"])
    data = [[Paragraph(f"<b>{h}</b>", styles["BodyMuted"]) for h in headers]]
    for r in rows:
        data.append([Paragraph(_fmt(cell, 80), styles["Body"]) for cell in r])
    t = Table(data, colWidths=col_widths)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), BG_TABLE_HEADER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.4, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    # Alternate row shading
    for i in range(2, len(data), 2):
        style.append(("BACKGROUND", (0, i), (-1, i), BG_TABLE_ALT))
    t.setStyle(TableStyle(style))
    return t


# ============ TOOL-SPECIFIC RENDERERS ============

def _render_port_scan(r, styles):
    story = [Paragraph(f"<b>Target:</b> {_fmt(r.get('target'))} &nbsp; "
                        f"<b>IP:</b> {_fmt(r.get('ip'))} &nbsp; "
                        f"<b>Mode:</b> {_fmt(r.get('mode'))} &nbsp; "
                        f"<b>Timing:</b> {_fmt(r.get('timing'))}",
                        styles["BodyMuted"])]
    story.append(Paragraph(f"Scanned <b>{r.get('ports_scanned')}</b> ports, "
                            f"found <b>{len(r.get('open_ports', []))}</b> open.",
                            styles["Body"]))
    story.append(Spacer(1, 4))
    rows = [[p.get("port"), p.get("service"), p.get("banner", "")[:60]]
            for p in r.get("open_ports", [])]
    story.append(_grid_table(["Port", "Service", "Banner"], rows, styles,
                              col_widths=[0.8*inch, 1.4*inch, 3.8*inch]))
    return story


def _render_dns_enum(r, styles):
    story = []
    for rtype, vals in (r.get("records") or {}).items():
        if not vals:
            continue
        story.append(Paragraph(f"<b>{rtype}</b>", styles["SectionH3"]))
        story.append(Paragraph("<br/>".join(_fmt(v, 200) for v in vals[:15]),
                                styles["Mono"]))
    extras = r.get("extras", {})
    if extras.get("zone_transfer", {}).get("vulnerable"):
        story.append(Paragraph("<b>&#9888; ZONE TRANSFER VULNERABLE</b>", styles["SectionH3"]))
    dnssec = extras.get("dnssec", {})
    if dnssec:
        status = "Enabled" if dnssec.get("enabled") else "Not enabled"
        story.append(Paragraph(f"<b>DNSSEC:</b> {status}", styles["Body"]))
    return story


def _render_subdomain(r, styles):
    story = [Paragraph(f"Found <b>{r.get('count', 0)}</b> subdomains from "
                        f"{', '.join(f'{k} ({v})' for k, v in (r.get('sources') or {}).items())}.",
                        styles["Body"])]
    subs = r.get("subdomains", [])[:40]
    if subs:
        story.append(Paragraph("<br/>".join(_fmt(s, 100) for s in subs), styles["Mono"]))
    if len(r.get("subdomains", [])) > 40:
        story.append(Paragraph(f"...and {len(r['subdomains']) - 40} more.", styles["BodyMuted"]))
    return story


def _render_whois(r, styles):
    w = r.get("whois", {})
    rows = [(k.replace("_", " ").title(), w[k]) for k in [
        "domain_name", "registrar", "creation_date", "expiration_date",
        "updated_date", "name_servers", "status", "emails",
        "org", "country", "registrant_name"
    ] if w.get(k)]
    return [_kv_table(rows, styles)]


def _render_dir_brute(r, styles):
    story = [Paragraph(f"Tested <b>{r.get('paths_tested')}</b> paths using "
                        f"<b>{r.get('wordlist_size')}</b> wordlist. "
                        f"Found <b>{len(r.get('found', []))}</b> interesting paths.",
                        styles["Body"])]
    rows = [[f.get("status"), f.get("path"), f.get("size"), f.get("server", "")]
            for f in r.get("found", [])[:30]]
    story.append(_grid_table(["Status", "Path", "Size", "Server"], rows, styles,
                              col_widths=[0.7*inch, 2.7*inch, 0.8*inch, 1.8*inch]))
    return story


def _render_web_crawler(r, styles):
    story = [_kv_table([
        ("Pages crawled", f"{r.get('pages_crawled')} / {r.get('pages_limit')}"),
        ("Total links", r.get("total_links")),
        ("Emails found", len(r.get("emails") or [])),
        ("Phones found", len(r.get("phones") or [])),
        ("Social profiles", len(r.get("social_profiles") or [])),
        ("External hosts", len(r.get("external_hosts") or [])),
        ("Forms", len(r.get("forms") or [])),
    ], styles)]
    if r.get("emails"):
        story.append(Paragraph("<b>Emails</b>", styles["SectionH3"]))
        story.append(Paragraph(", ".join(_fmt(e, 60) for e in r["emails"][:30]),
                                styles["Mono"]))
    return story


def _render_ssl_scan(r, styles):
    story = []
    grade = r.get("grade", {})
    if grade:
        story.append(Paragraph(
            f"<b>Grade: <font color='#{_grade_color(grade.get('grade')):06x}'>"
            f"{_fmt(grade.get('grade'))}</font></b> &nbsp; "
            f"Score: <b>{grade.get('score')}/100</b>",
            styles["SectionH3"]))
        if grade.get("issues"):
            story.append(Paragraph("<b>Issues:</b> " + "; ".join(grade["issues"]),
                                    styles["BodyMuted"]))
    rows = [
        ("TLS Version", r.get("tls_version")),
        ("Cipher", r.get("cipher_suite")),
        ("Bits", r.get("cipher_bits")),
        ("Self-signed", r.get("self_signed")),
        ("Not before", r.get("not_before")),
        ("Not after", r.get("not_after")),
        ("Days until expiry", r.get("days_until_expiry")),
        ("Issuer", r.get("issuer")),
        ("Subject", r.get("subject")),
        ("SAN", r.get("san")),
    ]
    story.append(_kv_table(rows, styles))
    return story


def _grade_color(grade):
    if not grade:
        return 0x94a3b8
    if grade.startswith("A"):
        return 0x059669
    if grade == "B":
        return 0x0891b2
    if grade in ("C", "D"):
        return 0xd97706
    return 0xdc2626


def _render_banner(r, styles):
    rows = [[x.get("port"), x.get("service"), (x.get("banner") or "")[:80]]
            for x in r.get("results", [])]
    return [_grid_table(["Port", "Service", "Banner"], rows, styles,
                         col_widths=[0.8*inch, 1.2*inch, 4*inch])]


def _render_username(r, styles):
    story = [Paragraph(f"Checked <b>{r.get('platforms_checked')}</b> platforms. "
                        f"Found on <b>{r.get('found_count', len(r.get('found_on', [])))}</b>.",
                        styles["Body"])]
    for cat, list_ in (r.get("found_by_category") or {}).items():
        story.append(Paragraph(f"<b>{cat.upper()}</b> ({len(list_)})", styles["SectionH3"]))
        rows = [[p.get("platform"), p.get("url")] for p in list_]
        story.append(_grid_table(["Platform", "URL"], rows, styles,
                                  col_widths=[1.5*inch, 4.3*inch]))
    if not r.get("found_by_category"):
        rows = [[p.get("platform"), p.get("url")] for p in r.get("found_on", [])]
        story.append(_grid_table(["Platform", "URL"], rows, styles,
                                  col_widths=[1.5*inch, 4.3*inch]))
    return story


def _render_email(r, styles):
    rows = [
        ("Email", r.get("email")),
        ("Valid syntax", r.get("valid_syntax")),
        ("Deliverable (MX)", r.get("deliverable")),
        ("Disposable", r.get("disposable")),
        ("Free provider", r.get("free_provider")),
        ("MX records", r.get("mx_records")),
        ("Has Gravatar", (r.get("gravatar") or {}).get("has_avatar")),
        ("HIBP breaches",
         (r.get("breaches") or {}).get("count", "N/A") if (r.get("breaches") or {}).get("available")
         else (r.get("breaches") or {}).get("reason", "not checked")),
    ]
    story = [_kv_table(rows, styles)]
    breaches = (r.get("breaches") or {}).get("breaches") or []
    if breaches:
        story.append(Paragraph("<b>Breach Details</b>", styles["SectionH3"]))
        rows = [[b.get("name"), b.get("date"), b.get("pwn_count"),
                 ", ".join(b.get("data_classes", []))] for b in breaches]
        story.append(_grid_table(
            ["Breach", "Date", "Accounts", "Data Exposed"], rows, styles,
            col_widths=[1.3*inch, 0.9*inch, 0.9*inch, 2.7*inch]))
    prof = (r.get("gravatar") or {}).get("profile")
    if prof:
        story.append(Paragraph("<b>Gravatar Profile</b>", styles["SectionH3"]))
        story.append(_kv_table([
            ("Display name", prof.get("display_name")),
            ("Location", prof.get("location")),
            ("Bio", prof.get("bio")),
        ], styles))
    return story


def _render_ip(r, styles):
    g = r.get("geolocation") or {}
    rows = [
        ("IP", r.get("ip")),
        ("Reverse DNS", r.get("reverse_dns")),
        ("Country", f"{g.get('country', '')} ({g.get('country_code', '')})"),
        ("Region / City", f"{g.get('region', '')}, {g.get('city', '')}"),
        ("Coordinates", f"{g.get('lat', '')}, {g.get('lon', '')}"),
        ("Timezone", g.get("timezone")),
        ("ISP / Org", f"{g.get('isp', '')} / {g.get('org', '')}"),
        ("ASN", g.get("asn")),
        ("Mobile", g.get("mobile")),
        ("Proxy / VPN", g.get("proxy")),
        ("Hosting", g.get("hosting")),
    ]
    story = [_kv_table(rows, styles)]

    abuse = r.get("abuse_reports") or {}
    if abuse.get("available"):
        story.append(Paragraph("<b>AbuseIPDB</b>", styles["SectionH3"]))
        story.append(_kv_table([
            ("Confidence score", abuse.get("abuse_confidence_score")),
            ("Total reports", abuse.get("total_reports")),
            ("Distinct users", abuse.get("num_distinct_users")),
            ("Last reported", abuse.get("last_reported")),
            ("Usage type", abuse.get("usage_type")),
            ("Is Tor", abuse.get("is_tor")),
        ], styles))

    shodan = r.get("shodan") or {}
    if shodan.get("available") and shodan.get("ports"):
        story.append(Paragraph("<b>Shodan Intelligence</b>", styles["SectionH3"]))
        story.append(_kv_table([
            ("OS", shodan.get("os")),
            ("Hostnames", shodan.get("hostnames")),
            ("Open ports", shodan.get("ports")),
            ("Vulnerabilities", shodan.get("vulns") or "None"),
            ("Tags", shodan.get("tags")),
        ], styles))
    return story


def _render_phone(r, styles):
    rows = [
        ("Number", r.get("target")),
        ("Valid", r.get("valid")),
        ("International", r.get("international")),
        ("E.164", r.get("e164")),
        ("Country code", f"+{r.get('country_code', '')}"),
        ("Region", r.get("region")),
        ("Carrier", r.get("carrier")),
        ("Line type", r.get("line_type")),
        ("Timezones", r.get("timezones")),
    ]
    return [_kv_table(rows, styles)]


def _render_metadata(r, styles):
    m = r.get("metadata") or {}
    rows = [
        ("Filename", r.get("filename")),
        ("Type", r.get("file_type")),
        ("Size", f"{r.get('size_bytes', 0):,} bytes"),
    ]
    if m.get("size"):
        rows.append(("Dimensions", f"{m['size'].get('width')} × {m['size'].get('height')}"))
    if m.get("gps_coordinates"):
        gps = m["gps_coordinates"]
        rows.append(("GPS", f"{gps.get('lat')}, {gps.get('lon')}"))
    story = [_kv_table(rows, styles)]

    if m.get("camera_summary"):
        story.append(Paragraph("<b>Camera & Copyright</b>", styles["SectionH3"]))
        story.append(_kv_table(list(m["camera_summary"].items()), styles))

    if m.get("exif"):
        story.append(Paragraph("<b>EXIF (top 20)</b>", styles["SectionH3"]))
        exif_items = list(m["exif"].items())[:20]
        story.append(_kv_table(exif_items, styles))

    if m.get("metadata"):
        story.append(Paragraph("<b>PDF Metadata</b>", styles["SectionH3"]))
        story.append(_kv_table(list(m["metadata"].items()), styles))
    return story


def _render_website(r, styles):
    rows = [
        ("Final URL", r.get("final_url")),
        ("Status", r.get("status_code")),
        ("Title", r.get("title")),
        ("Description", r.get("description")),
    ]
    story = [_kv_table(rows, styles)]

    if r.get("technologies"):
        story.append(Paragraph("<b>Technologies</b>", styles["SectionH3"]))
        story.append(Paragraph(", ".join(_fmt(t, 40) for t in r["technologies"]),
                                styles["Body"]))

    if r.get("trackers_detected"):
        story.append(Paragraph("<b>Trackers</b>", styles["SectionH3"]))
        story.append(Paragraph(", ".join(_fmt(t, 40) for t in r["trackers_detected"]),
                                styles["Body"]))

    if r.get("security_headers"):
        story.append(Paragraph("<b>Security Headers</b>", styles["SectionH3"]))
        rows = list(r["security_headers"].items())
        story.append(_kv_table(rows, styles))

    return story


def _render_generic(r, styles):
    """Fallback: dump top-level fields as key-value table."""
    filtered = [(k, v) for k, v in r.items()
                if k not in ("summary", "target") and v is not None]
    return [_kv_table(filtered[:15], styles)]


_TOOL_RENDERERS = {
    "port-scan": _render_port_scan,
    "dns-enum": _render_dns_enum,
    "subdomain-enum": _render_subdomain,
    "whois": _render_whois,
    "dir-brute": _render_dir_brute,
    "web-crawler": _render_web_crawler,
    "ssl-scan": _render_ssl_scan,
    "banner-grab": _render_banner,
    "username-lookup": _render_username,
    "email-investigation": _render_email,
    "ip-investigation": _render_ip,
    "phone-investigation": _render_phone,
    "metadata-extraction": _render_metadata,
    "website-analysis": _render_website,
}


# ============ MAIN BUILDER ============

def build_report(case: dict, investigator: str = "DFI Investigator") -> bytes:
    """Generate a professional PDF report for a case."""
    styles = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=0.75*inch, rightMargin=0.75*inch,
        topMargin=0.85*inch, bottomMargin=0.85*inch,
        title=f"DFI Report - {case.get('name', '')}",
        author=investigator,
    )

    story = []

    # ---------- COVER ----------
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph("Digital Footprint<br/>Investigation Report", styles["CoverTitle"]))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(_fmt(case.get("name", "Unnamed Case")), styles["CoverSubtitle"]))
    if case.get("primary_target"):
        story.append(Paragraph(f"Primary target: <b>{_fmt(case['primary_target'])}</b>",
                                styles["CoverMeta"]))
    story.append(Spacer(1, 1*inch))
    story.append(HRFlowable(width="40%", thickness=1, color=BRAND_PRIMARY,
                             hAlign="CENTER"))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(f"Investigator: <b>{_fmt(investigator)}</b>", styles["CoverMeta"]))
    story.append(Paragraph(f"Report generated: <b>{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</b>",
                            styles["CoverMeta"]))
    story.append(Paragraph(f"Case ID: <b>#{case.get('id', '?')}</b>", styles["CoverMeta"]))
    story.append(Paragraph(f"Case created: <b>{_fmt(case.get('created_at'))}</b>",
                            styles["CoverMeta"]))
    story.append(Spacer(1, 1.5*inch))
    story.append(Paragraph("<b>CONFIDENTIAL</b><br/>For authorized use only.",
                            styles["Small"]))
    story.append(PageBreak())

    # ---------- EXECUTIVE SUMMARY ----------
    story.append(Paragraph("Executive Summary", styles["SectionH1"]))
    results = case.get("results", [])
    entities = case.get("entities", [])
    successful = [r for r in results if r.get("status") == "success"]
    failed = [r for r in results if r.get("status") == "error"]

    entity_counts = {}
    for e in entities:
        entity_counts[e["entity_type"]] = entity_counts.get(e["entity_type"], 0) + 1

    summary_lines = [
        f"This investigation used <b>{len(results)}</b> tool runs "
        f"(<b>{len(successful)} successful</b>, <b>{len(failed)} failed</b>). ",
        f"A total of <b>{len(entities)}</b> distinct entities were identified.",
    ]
    if case.get("description"):
        summary_lines.insert(0, f"<i>{_fmt(case['description'], 400)}</i><br/><br/>")
    story.append(Paragraph("".join(summary_lines), styles["Summary"]))

    if entity_counts:
        story.append(Paragraph("Entities discovered:", styles["SectionH2"]))
        rows = [[etype.title(), count] for etype, count in
                sorted(entity_counts.items(), key=lambda x: -x[1])]
        story.append(_grid_table(["Entity Type", "Count"], rows, styles,
                                  col_widths=[3*inch, 1.5*inch]))

    if results:
        story.append(Paragraph("Tools executed:", styles["SectionH2"]))
        tool_summary = {}
        for r in results:
            tool_summary[r["tool_name"]] = tool_summary.get(r["tool_name"], 0) + 1
        rows = [[name, count] for name, count in
                sorted(tool_summary.items(), key=lambda x: -x[1])]
        story.append(_grid_table(["Tool", "Runs"], rows, styles,
                                  col_widths=[3*inch, 1.5*inch]))

    story.append(PageBreak())

    # ---------- ENTITIES ----------
    if entities:
        story.append(Paragraph("Identified Entities", styles["SectionH1"]))
        by_type = {}
        for e in entities:
            by_type.setdefault(e["entity_type"], []).append(e)

        for etype in sorted(by_type.keys()):
            story.append(Paragraph(f"{etype.title()} ({len(by_type[etype])})",
                                     styles["SectionH2"]))
            rows = [[e["value"], e.get("source_tool_id", "")]
                    for e in by_type[etype][:60]]
            story.append(_grid_table(["Value", "Source Tool"], rows, styles,
                                      col_widths=[3.8*inch, 2*inch]))
        story.append(PageBreak())

    # ---------- TOOL RESULTS ----------
    if successful:
        story.append(Paragraph("Detailed Findings", styles["SectionH1"]))
        for i, r in enumerate(successful):
            story.append(Paragraph(f"{i+1}. {_fmt(r['tool_name'])}", styles["SectionH2"]))
            story.append(Paragraph(
                f"<b>Target:</b> {_fmt(r.get('target'))} &nbsp;·&nbsp; "
                f"<b>Type:</b> {_fmt(r.get('tool_type'))} &nbsp;·&nbsp; "
                f"<b>Run at:</b> {_fmt(r.get('started_at'))}",
                styles["BodyMuted"]))
            if r.get("options"):
                opt_str = ", ".join(f"{k}={_fmt(v, 40)}" for k, v in r["options"].items() if v not in (None, ""))
                if opt_str:
                    story.append(Paragraph(f"<b>Options:</b> {opt_str}", styles["Small"]))

            data = r.get("result") or {}
            if data.get("summary"):
                story.append(Paragraph(f"<b>Summary:</b> {_fmt(data['summary'], 400)}",
                                        styles["Body"]))

            renderer = _TOOL_RENDERERS.get(r.get("tool_id"), _render_generic)
            try:
                content = renderer(data, styles)
            except Exception as e:
                content = [Paragraph(f"<i>Renderer error: {_fmt(e)}</i>", styles["Small"])]

            for flow in content:
                story.append(flow)
            story.append(Spacer(1, 12))
            story.append(HRFlowable(width="100%", thickness=0.3, color=BORDER))

    # ---------- FAILED SECTION ----------
    if failed:
        story.append(PageBreak())
        story.append(Paragraph("Failed / Errored Tool Runs", styles["SectionH1"]))
        for r in failed:
            story.append(Paragraph(f"<b>{_fmt(r['tool_name'])}</b> on "
                                     f"{_fmt(r.get('target'))}", styles["SectionH3"]))
            story.append(Paragraph(_fmt(r.get("error"), 400), styles["Small"]))

    # ---------- CHAIN OF CUSTODY ----------
    story.append(PageBreak())
    story.append(Paragraph("Chain of Custody", styles["SectionH1"]))
    story.append(Paragraph(
        "This report is generated automatically by the Digital Footprint "
        "Investigator toolkit. The SHA-256 fingerprint below can be used "
        "to verify report integrity. Any modification will change this hash.",
        styles["Body"]))
    # We'll insert hash placeholder for now — real hash computed after build below
    hash_placeholder = "__HASH_PLACEHOLDER__"
    story.append(Spacer(1, 20))
    story.append(Paragraph("Report SHA-256:", styles["SectionH3"]))
    story.append(Paragraph(f'<font face="Courier">{hash_placeholder}</font>', styles["Mono"]))
    story.append(Spacer(1, 30))
    story.append(Paragraph(f"Generated: {datetime.utcnow().isoformat()}Z", styles["Small"]))

    doc.build(story, onFirstPage=_draw_header_footer, onLaterPages=_draw_header_footer)

    pdf_bytes = buf.getvalue()

    # Compute hash of the (placeholder) PDF and replace it — simple integrity marker
    sha = hashlib.sha256(pdf_bytes).hexdigest()
    final_bytes = pdf_bytes.replace(hash_placeholder.encode(), sha.encode())
    return final_bytes
