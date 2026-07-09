"""
Generate a professional PowerPoint presentation for the
Digital-Footprint-Investigator project, matching the SWOC-style
design (dark gray/blue theme, hexagon illustrations, bullet points).

Usage
-----
    pip install python-pptx
    python generate_ppt.py

Output
------
    Digital-Footprint-Investigator-Presentation.pptx
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

# ==================== COLORS (from reference) ====================
DARK_BOX      = RGBColor(0x38, 0x38, 0x38)   # dark gray title box on cover
BLACK         = RGBColor(0x11, 0x11, 0x11)
WAVE_BLACK    = RGBColor(0x00, 0x00, 0x00)
BG_LIGHT      = RGBColor(0xD9, 0xD9, 0xD9)   # slide background
BORDER_GRAY   = RGBColor(0x8A, 0x8A, 0x8A)
HEX_BORDER    = RGBColor(0x8D, 0xA9, 0xC4)   # light blue hexagon outline
HEX_FILL      = RGBColor(0xFF, 0xFF, 0xFF)
BLUE_BOX      = RGBColor(0x82, 0xA6, 0xC7)   # section title box
WHITE         = RGBColor(0xFF, 0xFF, 0xFF)
TEXT_DARK     = RGBColor(0x1E, 0x1E, 0x1E)
TEXT_MUTED    = RGBColor(0x40, 0x40, 0x40)
ACCENT        = RGBColor(0x08, 0x91, 0xB2)

# ==================== SLIDE DIMENSIONS (16:9) ====================
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


# ==================== HELPERS ====================

def _set_fill(shape, rgb):
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb


def _no_fill(shape):
    shape.fill.background()


def _set_line(shape, rgb, width_pt=1.0):
    shape.line.color.rgb = rgb
    shape.line.width = Pt(width_pt)


def _no_line(shape):
    shape.line.fill.background()


def _add_text(shape, text, font_size, color=TEXT_DARK, bold=False,
              align=PP_ALIGN.LEFT, font_name="Georgia"):
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.1)
    tf.margin_right = Inches(0.1)
    tf.margin_top = Inches(0.05)
    tf.margin_bottom = Inches(0.05)
    tf.text = ""
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.name = font_name
    return tf


def _add_bullets(shape, items, font_size=18, color=TEXT_DARK, font_name="Georgia"):
    """Add bullet list where each item is a (heading, description) tuple
    or a plain string. Uses '❖' as bullet marker to match reference."""
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.15)
    tf.margin_right = Inches(0.15)
    tf.margin_top = Inches(0.15)
    tf.margin_bottom = Inches(0.15)
    tf.text = ""

    for idx, item in enumerate(items):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.space_after = Pt(8)

        # Bullet marker
        marker = p.add_run()
        marker.text = "❖  "
        marker.font.size = Pt(font_size)
        marker.font.color.rgb = TEXT_DARK
        marker.font.bold = True
        marker.font.name = font_name

        if isinstance(item, tuple) and len(item) == 2:
            head, desc = item
            head_run = p.add_run()
            head_run.text = head
            head_run.font.size = Pt(font_size)
            head_run.font.color.rgb = TEXT_DARK
            head_run.font.bold = True
            head_run.font.name = font_name

            body_run = p.add_run()
            body_run.text = ": " + desc
            body_run.font.size = Pt(font_size)
            body_run.font.color.rgb = TEXT_DARK
            body_run.font.name = font_name
        else:
            body_run = p.add_run()
            body_run.text = str(item)
            body_run.font.size = Pt(font_size)
            body_run.font.color.rgb = TEXT_DARK
            body_run.font.name = font_name
    return tf


def _add_shape(slide, shape_type, left, top, width, height):
    return slide.shapes.add_shape(shape_type, left, top, width, height)


def _add_slide(prs, blank=True):
    layout = prs.slide_layouts[6] if blank else prs.slide_layouts[0]  # blank
    return prs.slides.add_slide(layout)


def _add_slide_background(slide, rgb=BG_LIGHT):
    """Fill entire slide background."""
    bg = _add_shape(slide, MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
    _set_fill(bg, rgb)
    _no_line(bg)
    # Push to back
    spTree = bg._element.getparent()
    spTree.remove(bg._element)
    spTree.insert(2, bg._element)
    return bg


def _add_slide_border(slide, margin=Inches(0.25)):
    """Thin border rectangle just inside the slide edges."""
    border = _add_shape(slide, MSO_SHAPE.RECTANGLE,
                        margin, margin,
                        SLIDE_W - 2 * margin, SLIDE_H - 2 * margin)
    _no_fill(border)
    _set_line(border, BORDER_GRAY, 0.75)
    return border


def _add_footer(slide, name="Ravi Pandit", roll="12401796"):
    """Bottom-left footer with name + roll number."""
    tb = slide.shapes.add_textbox(Inches(0.5), Inches(6.65),
                                   Inches(3.5), Inches(0.7))
    tf = tb.text_frame
    tf.margin_top = 0
    tf.margin_bottom = 0
    tf.text = ""
    p = tf.paragraphs[0]
    r1 = p.add_run(); r1.text = name
    r1.font.size = Pt(16); r1.font.color.rgb = TEXT_MUTED; r1.font.name = "Georgia"
    p2 = tf.add_paragraph()
    r2 = p2.add_run(); r2.text = roll
    r2.font.size = Pt(16); r2.font.color.rgb = TEXT_MUTED; r2.font.name = "Georgia"
    return tb


def _add_corner_marker(slide):
    """Small blue triangle indicator in bottom-right corner (as in reference)."""
    marker = _add_shape(slide, MSO_SHAPE.RIGHT_TRIANGLE,
                        SLIDE_W - Inches(0.35), SLIDE_H - Inches(0.35),
                        Inches(0.28), Inches(0.28))
    _set_fill(marker, BLUE_BOX)
    _no_line(marker)


# ==================== SLIDE BUILDERS ====================

def build_title_slide(prs, title, subtitle):
    """
    Cover slide: white background, wide horizontal stripes suggesting a wave,
    large black wave at bottom, dark gray title box centered-left with white text.
    """
    slide = _add_slide(prs)

    # White base
    _add_slide_background(slide, WHITE)

    # Striped middle band — many thin gray horizontal rectangles
    stripe_start_y = Inches(3.4)
    stripe_gap = Inches(0.09)
    stripe_thickness = Inches(0.05)
    for i in range(18):
        y = stripe_start_y + i * stripe_gap
        stripe = _add_shape(slide, MSO_SHAPE.RECTANGLE, 0, y, SLIDE_W, stripe_thickness)
        _set_fill(stripe, RGBColor(0x60, 0x60, 0x60))
        _no_line(stripe)

    # Solid black wave-like base at bottom (using cloud-like curved shape)
    wave = _add_shape(slide, MSO_SHAPE.WAVE, 0, Inches(5.8),
                      SLIDE_W, Inches(1.9))
    _set_fill(wave, WAVE_BLACK)
    _no_line(wave)

    # Dark gray title card (centered-left)
    box_w, box_h = Inches(7.5), Inches(3.5)
    box_x = Inches(1.4)
    box_y = Inches(1.9)
    card = _add_shape(slide, MSO_SHAPE.RECTANGLE, box_x, box_y, box_w, box_h)
    _set_fill(card, DARK_BOX)
    _no_line(card)

    # Inner thin border inside the card
    inner_pad = Inches(0.2)
    inner = _add_shape(slide, MSO_SHAPE.RECTANGLE,
                       box_x + inner_pad, box_y + inner_pad,
                       box_w - 2 * inner_pad, box_h - 2 * inner_pad)
    _no_fill(inner)
    _set_line(inner, WHITE, 0.75)

    # Title text
    tbox = slide.shapes.add_textbox(box_x + Inches(0.5), box_y + Inches(0.7),
                                     box_w - Inches(1), Inches(1.5))
    tf = tbox.text_frame
    tf.margin_left = 0; tf.margin_right = 0
    tf.text = ""
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = title
    r.font.size = Pt(40); r.font.color.rgb = WHITE
    r.font.name = "Georgia"; r.font.bold = False

    # Subtitle
    sbox = slide.shapes.add_textbox(box_x + Inches(0.5), box_y + Inches(2.3),
                                     box_w - Inches(1), Inches(0.6))
    stf = sbox.text_frame
    stf.margin_left = 0; stf.margin_right = 0
    stf.text = ""
    sp = stf.paragraphs[0]
    sp.alignment = PP_ALIGN.CENTER
    sr = sp.add_run(); sr.text = subtitle
    sr.font.size = Pt(20); sr.font.color.rgb = WHITE
    sr.font.name = "Georgia"


def build_content_slide(prs, section_title, bullets, hex_symbol="\u25C6",
                         hex_symbol_size=140):
    """
    Standard content slide: gray bg + border, hexagon with icon on left,
    blue title box in top-right, two decorative white hexagons, bullets on right,
    footer bottom-left.

    bullets: list of (heading, description) tuples OR plain strings.
    """
    slide = _add_slide(prs)

    # Gray background + inner border
    _add_slide_background(slide, BG_LIGHT)
    _add_slide_border(slide)

    # ===== BIG HEXAGON on left =====
    hex_x = Inches(0.9)
    hex_y = Inches(1.1)
    hex_w = Inches(5.6)
    hex_h = Inches(5.2)
    big_hex = _add_shape(slide, MSO_SHAPE.HEXAGON, hex_x, hex_y, hex_w, hex_h)
    _set_fill(big_hex, HEX_FILL)
    _set_line(big_hex, HEX_BORDER, 2.0)

    # Icon/symbol inside the hexagon (large glyph as visual placeholder)
    icon_box = slide.shapes.add_textbox(hex_x, hex_y + Inches(1.2),
                                         hex_w, Inches(3.0))
    itf = icon_box.text_frame
    itf.margin_top = 0; itf.margin_bottom = 0
    itf.text = ""
    ip = itf.paragraphs[0]
    ip.alignment = PP_ALIGN.CENTER
    ir = ip.add_run(); ir.text = hex_symbol
    ir.font.size = Pt(hex_symbol_size)
    ir.font.color.rgb = BLUE_BOX
    ir.font.name = "Segoe UI Emoji"

    # ===== BLUE TITLE BOX (top right) =====
    tb_x = Inches(8.3)
    tb_y = Inches(0.85)
    tb_w = Inches(4.3)
    tb_h = Inches(0.75)
    title_box = _add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE,
                            tb_x, tb_y, tb_w, tb_h)
    _set_fill(title_box, BLUE_BOX)
    _set_line(title_box, WHITE, 0.75)
    _add_text(title_box, section_title, font_size=22, color=WHITE,
              bold=False, align=PP_ALIGN.CENTER, font_name="Georgia")
    title_box.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE

    # ===== Two decorative white hexagons floating left of title box =====
    dec1 = _add_shape(slide, MSO_SHAPE.HEXAGON,
                       Inches(7.2), Inches(1.55), Inches(0.7), Inches(0.6))
    _set_fill(dec1, WHITE)
    _set_line(dec1, HEX_BORDER, 1.0)

    dec2 = _add_shape(slide, MSO_SHAPE.HEXAGON,
                       Inches(7.8), Inches(1.1), Inches(0.7), Inches(0.6))
    _set_fill(dec2, WHITE)
    _set_line(dec2, HEX_BORDER, 1.0)

    # ===== BULLETS on right =====
    body_box = slide.shapes.add_textbox(Inches(6.8), Inches(2.2),
                                         Inches(6.2), Inches(4.4))
    _add_bullets(body_box, bullets, font_size=17)

    # ===== Footer + corner marker =====
    _add_footer(slide)
    _add_corner_marker(slide)


def build_closing_slide(prs, big_text="THANK YOU", subtitle="Digital Footprint Investigator"):
    """Simple thank-you slide with the cover style."""
    slide = _add_slide(prs)

    _add_slide_background(slide, WHITE)

    # Striped middle band
    stripe_start_y = Inches(3.4)
    stripe_gap = Inches(0.09)
    for i in range(18):
        y = stripe_start_y + i * stripe_gap
        stripe = _add_shape(slide, MSO_SHAPE.RECTANGLE, 0, y, SLIDE_W, Inches(0.05))
        _set_fill(stripe, RGBColor(0x60, 0x60, 0x60))
        _no_line(stripe)

    wave = _add_shape(slide, MSO_SHAPE.WAVE, 0, Inches(5.8),
                      SLIDE_W, Inches(1.9))
    _set_fill(wave, WAVE_BLACK)
    _no_line(wave)

    # Card
    box_w, box_h = Inches(7.5), Inches(3.5)
    box_x = Inches(2.9)
    box_y = Inches(1.9)
    card = _add_shape(slide, MSO_SHAPE.RECTANGLE, box_x, box_y, box_w, box_h)
    _set_fill(card, DARK_BOX)
    _no_line(card)

    inner_pad = Inches(0.2)
    inner = _add_shape(slide, MSO_SHAPE.RECTANGLE,
                       box_x + inner_pad, box_y + inner_pad,
                       box_w - 2 * inner_pad, box_h - 2 * inner_pad)
    _no_fill(inner)
    _set_line(inner, WHITE, 0.75)

    tbox = slide.shapes.add_textbox(box_x + Inches(0.5), box_y + Inches(0.9),
                                     box_w - Inches(1), Inches(1.5))
    tf = tbox.text_frame; tf.text = ""
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = big_text
    r.font.size = Pt(52); r.font.color.rgb = WHITE
    r.font.name = "Georgia"

    sbox = slide.shapes.add_textbox(box_x + Inches(0.5), box_y + Inches(2.3),
                                     box_w - Inches(1), Inches(0.6))
    stf = sbox.text_frame; stf.text = ""
    sp = stf.paragraphs[0]; sp.alignment = PP_ALIGN.CENTER
    sr = sp.add_run(); sr.text = subtitle
    sr.font.size = Pt(20); sr.font.color.rgb = WHITE
    sr.font.name = "Georgia"


# ==================== BUILD PRESENTATION ====================

def build():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    # ---------- 1. TITLE ----------
    build_title_slide(
        prs,
        title="DIGITAL FOOTPRINT INVESTIGATOR",
        subtitle="RAVI PANDIT"
    )

    # ---------- 2. ABOUT THE PROJECT ----------
    build_content_slide(
        prs,
        section_title="ABOUT THE PROJECT",
        hex_symbol="\U0001F50D",  # magnifying glass
        bullets=[
            ("What it is",
             "An OSINT toolkit for investigating digital identities across the web."),
            ("Architecture",
             "Web-based UI backed by a Python Flask API with SQLite storage."),
            ("Scope",
             "22 professional tools covering active recon and passive intelligence."),
        ]
    )

    # ---------- 3. PROBLEM STATEMENT ----------
    build_content_slide(
        prs,
        section_title="PROBLEM STATEMENT",
        hex_symbol="\u26A0",  # warning
        bullets=[
            ("Fragmented workflow",
             "Investigators use dozens of scattered tools with inconsistent output."),
            ("Manual & slow",
             "OSINT gathering by hand is time-consuming and error-prone."),
            ("No unified reporting",
             "Findings are hard to consolidate into a professional report."),
        ]
    )

    # ---------- 4. OBJECTIVES ----------
    build_content_slide(
        prs,
        section_title="OBJECTIVES",
        hex_symbol="\U0001F3AF",  # dart
        bullets=[
            ("Unified toolkit",
             "Build a single-window OSINT platform with a clean, modern UI."),
            ("Automation",
             "Automate discovery, correlation, and enrichment of digital footprints."),
            ("Professional output",
             "Enable one-click generation of PDF investigation reports."),
        ]
    )

    # ---------- 5. UI DESIGN — 3 SECTIONS ----------
    build_content_slide(
        prs,
        section_title="USER INTERFACE",
        hex_symbol="\U0001F5A5",  # desktop
        bullets=[
            ("Active section",
             "Tools that directly interact with a target — scans, brute force, crawlers."),
            ("Passive section",
             "Non-intrusive intelligence gathering from public sources and APIs."),
            ("Results section",
             "Unified view with filters, entity chips, and export options."),
        ]
    )

    # ---------- 6. TOOLS OVERVIEW ----------
    build_content_slide(
        prs,
        section_title="22 POWERFUL TOOLS",
        hex_symbol="\U0001F6E0",  # hammer and wrench
        bullets=[
            ("8 Active tools",
             "Port Scan, DNS Enum, Subdomain, WHOIS, Dir Brute, Crawler, SSL, Banner."),
            ("14 Passive tools",
             "Username, Email, Phone, Domain, IP, Metadata, Website Analysis, more."),
            ("Extended OSINT",
             "Breach Check, Reverse Image, Google Dorking, Dark Web Monitor."),
        ]
    )

    # ---------- 7. TECHNOLOGY STACK ----------
    build_content_slide(
        prs,
        section_title="TECHNOLOGY STACK",
        hex_symbol="\u2699",  # gear
        bullets=[
            ("Backend",
             "Python 3, Flask, SQLite, ReportLab, dnspython, phonenumbers, Pillow."),
            ("Frontend",
             "HTML5, modern CSS, vanilla JavaScript — zero-build, works anywhere."),
            ("Deployment",
             "Docker Compose for one-command setup — cross-platform on Linux, Windows, Mac."),
        ]
    )

    # ---------- 8. PROFESSIONAL FEATURES: CASES & PDF ----------
    build_content_slide(
        prs,
        section_title="INVESTIGATION CASES",
        hex_symbol="\U0001F4C1",  # folder
        bullets=[
            ("SQLite persistence",
             "Every scan is saved under a case — results survive reloads and restarts."),
            ("Entity correlation",
             "Auto-extracts emails, IPs, domains, usernames, GPS coordinates from output."),
            ("Smart suggestions",
             "Recommends the next tool to run based on discovered entities."),
        ]
    )

    # ---------- 9. PDF REPORTS ----------
    build_content_slide(
        prs,
        section_title="PDF REPORTS",
        hex_symbol="\U0001F4C4",  # page facing up
        bullets=[
            ("Multi-page format",
             "Branded cover, executive summary, entity index, per-tool findings."),
            ("Specialized renderers",
             "Custom formatting per tool — SSL grade cards, breach tables, GPS maps."),
            ("Chain of custody",
             "SHA-256 fingerprint on every report to verify integrity of evidence."),
        ]
    )

    # ---------- 10. UX FEATURES ----------
    build_content_slide(
        prs,
        section_title="UX HIGHLIGHTS",
        hex_symbol="\U0001F3A8",  # artist palette
        bullets=[
            ("Command palette",
             "Ctrl+K opens fuzzy search across tools, cases, and quick actions."),
            ("Dark & light themes",
             "Toggle in header, syncs with OS preference, persists across sessions."),
            ("Basic vs Advanced",
             "Every tool has configurable options with sensible defaults."),
        ]
    )

    # ---------- 11. USE CASES ----------
    build_content_slide(
        prs,
        section_title="USE CASES",
        hex_symbol="\U0001F465",  # busts silhouette
        bullets=[
            ("Cybersecurity teams",
             "Reconnaissance during authorized penetration tests and red team ops."),
            ("Digital forensics",
             "Building consolidated investigation reports with evidence trails."),
            ("Education & training",
             "Learning OSINT methodology in a structured, tool-guided environment."),
        ]
    )

    # ---------- 12. FUTURE SCOPE ----------
    build_content_slide(
        prs,
        section_title="FUTURE SCOPE",
        hex_symbol="\U0001F680",  # rocket
        bullets=[
            ("Team collaboration",
             "Multi-user authentication, shared cases, and comments on findings."),
            ("Machine learning",
             "Anomaly detection, target classification, and automated risk scoring."),
            ("Real-time scaling",
             "Background job queue, WebSocket streaming, and threat feed integrations."),
        ]
    )

    # ---------- 13. THANK YOU ----------
    build_closing_slide(prs, big_text="THANK YOU",
                         subtitle="Digital Footprint Investigator")

    out = "Digital-Footprint-Investigator-Presentation.pptx"
    prs.save(out)
    print(f"[OK] Saved {out}")
    print(f"    Slides: {len(prs.slides)}")


if __name__ == "__main__":
    build()
