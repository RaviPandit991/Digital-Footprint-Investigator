"""
Generate a ~20-page project report (Microsoft Word .docx) for the
Digital Footprint Investigator project.

The generated report is fully editable in Microsoft Word so you can
change text, add screenshots, rename sections, etc.

Usage
-----
    pip install python-docx
    python generate_report.py

Output
------
    Digital-Footprint-Investigator-Report.docx
"""
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


# ========================================================================
#                              CONFIG
# ========================================================================

STUDENT_NAME = "Ravi Pandit"
ROLL_NUMBER = "12401796"
COURSE = "B.Tech Computer Science and Engineering"
UNIVERSITY = "Lovely Professional University"
GUIDE_NAME = "[Guide Name Here]"
SUBMISSION_MONTH = "November 2026"
PROJECT_TITLE = "Digital Footprint Investigator"
PROJECT_SUBTITLE = "An OSINT Toolkit for Digital Identity Investigation"

OUTPUT = "Digital-Footprint-Investigator-Report.docx"


# ========================================================================
#                            DOCX HELPERS
# ========================================================================

def set_default_font(doc, name="Times New Roman", size=12):
    """Set Times New Roman 12pt as default style."""
    style = doc.styles["Normal"]
    style.font.name = name
    style.font.size = Pt(size)
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), name)
    rfonts.set(qn("w:hAnsi"), name)
    rfonts.set(qn("w:eastAsia"), name)
    rfonts.set(qn("w:cs"), name)


def set_margins(doc, top=1.0, bottom=1.0, left=1.25, right=1.0):
    """Set page margins in inches."""
    for section in doc.sections:
        section.top_margin = Inches(top)
        section.bottom_margin = Inches(bottom)
        section.left_margin = Inches(left)
        section.right_margin = Inches(right)


def add_page_number(doc):
    """Add page number to footer."""
    section = doc.sections[0]
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    run = p.add_run()
    fldChar1 = OxmlElement("w:fldChar")
    fldChar1.set(qn("w:fldCharType"), "begin")
    instrText = OxmlElement("w:instrText")
    instrText.set(qn("xml:space"), "preserve")
    instrText.text = "PAGE"
    fldChar2 = OxmlElement("w:fldChar")
    fldChar2.set(qn("w:fldCharType"), "end")
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)


def add_para(doc, text, style="Normal", align=None, bold=False,
             italic=False, size=None, color=None, space_after=6,
             line_spacing=1.5, first_line_indent=None):
    """Add a paragraph with formatting."""
    p = doc.add_paragraph(style=style)
    if align:
        p.alignment = align
    if space_after is not None:
        p.paragraph_format.space_after = Pt(space_after)
    if line_spacing:
        p.paragraph_format.line_spacing = line_spacing
    if first_line_indent:
        p.paragraph_format.first_line_indent = Inches(first_line_indent)
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    if size:
        run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if color:
        run.font.color.rgb = color
    return p


def add_heading1(doc, text):
    """Chapter heading: e.g. 'CHAPTER 1: INTRODUCTION'."""
    doc.add_page_break()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(18)
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(18)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x1F, 0x3A, 0x60)


def add_heading2(doc, text):
    """Section heading: e.g. '1.1 Overview'."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x2C, 0x5A, 0x8F)


def add_heading3(doc, text):
    """Subsection heading: e.g. '1.1.1 Functional Requirements'."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(12)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)


def add_body(doc, text, first_line_indent=0.3):
    """Justified body paragraph."""
    return add_para(doc, text, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
                    first_line_indent=first_line_indent, line_spacing=1.5,
                    space_after=6)


def add_bullets(doc, items, indent=0.25):
    """Add bullet list."""
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.left_indent = Inches(indent)
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(item)
        run.font.name = "Times New Roman"
        run.font.size = Pt(12)


def add_numbered(doc, items, indent=0.25):
    """Add numbered list."""
    for item in items:
        p = doc.add_paragraph(style="List Number")
        p.paragraph_format.left_indent = Inches(indent)
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(item)
        run.font.name = "Times New Roman"
        run.font.size = Pt(12)


def add_table(doc, header, rows, col_widths=None):
    """Add a formatted table."""
    tbl = doc.add_table(rows=1 + len(rows), cols=len(header))
    tbl.style = "Light Grid Accent 1"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Header row
    for i, h in enumerate(header):
        cell = tbl.rows[0].cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(h)
        run.font.bold = True
        run.font.size = Pt(11)
        run.font.name = "Times New Roman"

    # Data rows
    for r_idx, row in enumerate(rows, start=1):
        for c_idx, value in enumerate(row):
            cell = tbl.rows[r_idx].cells[c_idx]
            cell.text = ""
            p = cell.paragraphs[0]
            run = p.add_run(str(value))
            run.font.size = Pt(11)
            run.font.name = "Times New Roman"

    if col_widths:
        for row in tbl.rows:
            for i, w in enumerate(col_widths):
                row.cells[i].width = Inches(w)

    # Add small spacer paragraph after the table
    doc.add_paragraph()
    return tbl


def add_code_block(doc, code):
    """Add a monospace code snippet in a shaded box."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.3)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.15
    for line in code.strip("\n").split("\n"):
        run = p.add_run(line + "\n")
        run.font.name = "Consolas"
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)


def add_figure_placeholder(doc, caption):
    """Placeholder box for a figure/screenshot to be inserted by user."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f"[ INSERT SCREENSHOT: {caption} HERE ]")
    run.font.italic = True
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(0x88, 0x88, 0x88)

    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cr = cap.add_run(f"Fig: {caption}")
    cr.font.size = Pt(10)
    cr.font.italic = True
    cr.font.name = "Times New Roman"


# ========================================================================
#                          SECTION BUILDERS
# ========================================================================

def build_cover_page(doc):
    for _ in range(2):
        doc.add_paragraph()

    add_para(doc, "A PROJECT REPORT ON", align=WD_ALIGN_PARAGRAPH.CENTER,
             bold=True, size=14, line_spacing=1.5, space_after=12)

    add_para(doc, PROJECT_TITLE, align=WD_ALIGN_PARAGRAPH.CENTER,
             bold=True, size=28, line_spacing=1.2, space_after=6,
             color=RGBColor(0x1F, 0x3A, 0x60))

    add_para(doc, PROJECT_SUBTITLE, align=WD_ALIGN_PARAGRAPH.CENTER,
             italic=True, size=14, space_after=36,
             color=RGBColor(0x55, 0x55, 0x55))

    add_para(doc, "Submitted in partial fulfillment of the requirements "
             "for the award of the degree of", align=WD_ALIGN_PARAGRAPH.CENTER,
             size=12, space_after=6)

    add_para(doc, "BACHELOR OF TECHNOLOGY", align=WD_ALIGN_PARAGRAPH.CENTER,
             bold=True, size=14, space_after=6)

    add_para(doc, "IN COMPUTER SCIENCE AND ENGINEERING",
             align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=13,
             space_after=36)

    add_para(doc, "Submitted By", align=WD_ALIGN_PARAGRAPH.CENTER,
             size=12, space_after=6)
    add_para(doc, STUDENT_NAME, align=WD_ALIGN_PARAGRAPH.CENTER,
             bold=True, size=14, space_after=2)
    add_para(doc, f"Registration No: {ROLL_NUMBER}",
             align=WD_ALIGN_PARAGRAPH.CENTER, size=12, space_after=24)

    add_para(doc, "Under the Guidance of", align=WD_ALIGN_PARAGRAPH.CENTER,
             size=12, space_after=6)
    add_para(doc, GUIDE_NAME, align=WD_ALIGN_PARAGRAPH.CENTER,
             bold=True, size=13, space_after=48)

    add_para(doc, "[ UNIVERSITY LOGO ]", align=WD_ALIGN_PARAGRAPH.CENTER,
             italic=True, size=10, space_after=24,
             color=RGBColor(0x88, 0x88, 0x88))

    add_para(doc, UNIVERSITY.upper(), align=WD_ALIGN_PARAGRAPH.CENTER,
             bold=True, size=16, space_after=6,
             color=RGBColor(0x1F, 0x3A, 0x60))
    add_para(doc, "School of Computer Science and Engineering",
             align=WD_ALIGN_PARAGRAPH.CENTER, size=12, space_after=6)
    add_para(doc, SUBMISSION_MONTH, align=WD_ALIGN_PARAGRAPH.CENTER,
             size=12, space_after=6)


def build_certificate(doc):
    doc.add_page_break()
    add_para(doc, "CERTIFICATE", align=WD_ALIGN_PARAGRAPH.CENTER,
             bold=True, size=20, space_after=24,
             color=RGBColor(0x1F, 0x3A, 0x60))

    body = (
        f"This is to certify that the project report titled "
        f"\"{PROJECT_TITLE}\" is a bonafide work carried out by "
        f"{STUDENT_NAME} (Registration No: {ROLL_NUMBER}) in partial "
        f"fulfillment of the requirements for the award of the degree "
        f"of Bachelor of Technology in Computer Science and Engineering "
        f"from {UNIVERSITY}, during the academic year 2025-2026.\n\n"
        f"To the best of my knowledge, the work presented in this report "
        f"has not been submitted to any other university or institution "
        f"for the award of any degree or diploma. The candidate has "
        f"worked sincerely and made significant progress throughout the "
        f"project development period."
    )
    add_body(doc, body)

    for _ in range(6):
        doc.add_paragraph()

    # Signature block
    tbl = doc.add_table(rows=2, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.rows[0].cells[0].text = "____________________"
    tbl.rows[0].cells[1].text = "____________________"
    tbl.rows[1].cells[0].text = f"{GUIDE_NAME}\n(Project Guide)"
    tbl.rows[1].cells[1].text = "Head of Department\nComputer Science and Engineering"
    for row in tbl.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER


def build_declaration(doc):
    doc.add_page_break()
    add_para(doc, "DECLARATION", align=WD_ALIGN_PARAGRAPH.CENTER,
             bold=True, size=20, space_after=24,
             color=RGBColor(0x1F, 0x3A, 0x60))

    body = (
        f"I, {STUDENT_NAME} (Registration No: {ROLL_NUMBER}), hereby "
        f"declare that the project report titled \"{PROJECT_TITLE}\" is "
        f"an original piece of work carried out by me under the guidance "
        f"of {GUIDE_NAME}, {UNIVERSITY}.\n\n"
        f"I further declare that this report has not been submitted "
        f"either in part or in full to any other university or "
        f"institution for the award of any degree, diploma, or similar "
        f"title. All sources of information used in the preparation of "
        f"this report have been duly acknowledged.\n\n"
        f"I understand that any violation of the above declaration will "
        f"be treated as academic misconduct and may lead to disciplinary "
        f"action as per the norms of the university."
    )
    add_body(doc, body)

    for _ in range(6):
        doc.add_paragraph()

    add_para(doc, f"Place: __________________",
             align=WD_ALIGN_PARAGRAPH.LEFT, size=12, space_after=6)
    add_para(doc, f"Date: ___________________",
             align=WD_ALIGN_PARAGRAPH.LEFT, size=12, space_after=24)
    add_para(doc, "____________________________",
             align=WD_ALIGN_PARAGRAPH.RIGHT, size=12, space_after=2)
    add_para(doc, f"{STUDENT_NAME}", align=WD_ALIGN_PARAGRAPH.RIGHT,
             bold=True, size=12, space_after=2)
    add_para(doc, f"Registration No: {ROLL_NUMBER}",
             align=WD_ALIGN_PARAGRAPH.RIGHT, size=12, space_after=2)


def build_acknowledgment(doc):
    doc.add_page_break()
    add_para(doc, "ACKNOWLEDGMENT", align=WD_ALIGN_PARAGRAPH.CENTER,
             bold=True, size=20, space_after=24,
             color=RGBColor(0x1F, 0x3A, 0x60))

    paras = [
        "The successful completion of this project would not have been "
        "possible without the support, guidance, and encouragement of "
        "several individuals, and I take this opportunity to express my "
        "sincere gratitude to each of them.",

        f"First and foremost, I extend my deepest gratitude to my project "
        f"guide, {GUIDE_NAME}, for the invaluable guidance, constructive "
        f"criticism, and continuous encouragement provided throughout the "
        f"development of this project. Their expertise and insight helped "
        f"me refine both the technical implementation and the overall "
        f"presentation of this work.",

        f"I would like to thank the Head of the Department and the entire "
        f"faculty of the School of Computer Science and Engineering, "
        f"{UNIVERSITY}, for providing me with the necessary infrastructure, "
        f"laboratory facilities, and academic environment that enabled me "
        f"to carry out this project.",

        "I am also grateful to the open-source community whose libraries, "
        "tools, and public documentation formed the foundation of this "
        "work. Special thanks to the maintainers of Flask, python-whois, "
        "dnspython, phonenumbers, Pillow, ReportLab, and the many other "
        "libraries that made this project possible.",

        "Finally, I would like to thank my family and friends for their "
        "constant support, motivation, and patience during the long "
        "hours spent building and testing this project. Their belief in "
        "me was a source of great strength.",
    ]
    for p in paras:
        add_body(doc, p)

    for _ in range(4):
        doc.add_paragraph()

    add_para(doc, STUDENT_NAME, align=WD_ALIGN_PARAGRAPH.RIGHT,
             bold=True, size=12, space_after=2)
    add_para(doc, f"Registration No: {ROLL_NUMBER}",
             align=WD_ALIGN_PARAGRAPH.RIGHT, size=12)


def build_abstract(doc):
    doc.add_page_break()
    add_para(doc, "ABSTRACT", align=WD_ALIGN_PARAGRAPH.CENTER,
             bold=True, size=20, space_after=24,
             color=RGBColor(0x1F, 0x3A, 0x60))

    paras = [
        "In today's hyper-connected digital world, individuals and "
        "organizations leave behind vast trails of information across "
        "social networks, websites, public registries, and technical "
        "infrastructure records. This information, collectively known as "
        "a digital footprint, is of significant interest to cybersecurity "
        "professionals, digital forensic investigators, journalists, and "
        "law enforcement agencies who work in the field of Open Source "
        "Intelligence, or OSINT.",

        "Currently, OSINT investigators rely on dozens of scattered tools "
        "with inconsistent user interfaces, output formats, and workflows. "
        "This fragmentation slows down investigations, increases the "
        "likelihood of missed evidence, and makes generating professional "
        "reports a manual, error-prone process. There is a clear need for "
        "a unified platform that consolidates common OSINT techniques "
        "under a single, well-designed user interface with automated "
        "correlation of findings and streamlined reporting.",

        "This project, titled Digital Footprint Investigator, addresses "
        "this gap by presenting a full-stack web application that "
        "integrates 22 distinct OSINT tools. These tools are organized "
        "into two categories: eight active reconnaissance tools that "
        "directly interact with a target, such as port scanning and "
        "directory brute-forcing, and fourteen passive intelligence tools "
        "that gather data exclusively from public sources, such as "
        "username lookup across 90 platforms, email breach checking, and "
        "certificate transparency-based subdomain enumeration.",

        "The system is built with a modular Python Flask backend, a "
        "modern responsive frontend using vanilla JavaScript, and a "
        "SQLite persistence layer that automatically groups tool "
        "invocations under investigation cases. Every successful tool "
        "run passes through an entity extraction module that identifies "
        "structured data such as emails, IP addresses, subdomains, and "
        "GPS coordinates, and feeds these into a suggestion engine that "
        "recommends the most relevant next tool to run. The system also "
        "generates professional multi-page PDF reports with a "
        "SHA-256 chain-of-custody hash, ships with a Ctrl+K command "
        "palette for rapid tool access, and can be deployed with a "
        "single Docker Compose command.",

        "The system has been tested against a variety of publicly "
        "authorized targets and has demonstrated reliable, correct "
        "operation across all 22 tools. This report presents the "
        "motivation, design, implementation, and evaluation of the "
        "system in detail, along with the technical concepts that "
        "underpin its operation.",

        "Keywords: OSINT, Cybersecurity, Digital Forensics, Reconnaissance, "
        "Python, Flask, SQLite, Docker, Web Application, Entity Correlation.",
    ]
    for p in paras:
        add_body(doc, p)


def build_toc(doc):
    doc.add_page_break()
    add_para(doc, "TABLE OF CONTENTS", align=WD_ALIGN_PARAGRAPH.CENTER,
             bold=True, size=20, space_after=24,
             color=RGBColor(0x1F, 0x3A, 0x60))

    toc_entries = [
        ("Certificate", "ii"),
        ("Declaration", "iii"),
        ("Acknowledgment", "iv"),
        ("Abstract", "v"),
        ("Table of Contents", "vi"),
        ("List of Figures", "vii"),
        ("List of Tables", "viii"),
        ("", ""),
        ("Chapter 1: Introduction", "1"),
        ("    1.1 Overview", "1"),
        ("    1.2 Motivation", "2"),
        ("    1.3 Problem Statement", "3"),
        ("    1.4 Objectives", "3"),
        ("    1.5 Scope of the Project", "4"),
        ("    1.6 Organization of the Report", "4"),
        ("", ""),
        ("Chapter 2: Literature Review", "5"),
        ("    2.1 Introduction to OSINT", "5"),
        ("    2.2 Existing Tools and Their Limitations", "6"),
        ("    2.3 Research Gap", "7"),
        ("", ""),
        ("Chapter 3: System Analysis", "8"),
        ("    3.1 Requirement Analysis", "8"),
        ("    3.2 Feasibility Study", "9"),
        ("    3.3 System Requirements", "10"),
        ("", ""),
        ("Chapter 4: System Design", "11"),
        ("    4.1 Architectural Overview", "11"),
        ("    4.2 Database Design", "12"),
        ("    4.3 API Design", "13"),
        ("    4.4 User Interface Design", "13"),
        ("", ""),
        ("Chapter 5: Technology Stack", "14"),
        ("", ""),
        ("Chapter 6: Implementation", "15"),
        ("    6.1 Project Structure", "15"),
        ("    6.2 Active Tools", "16"),
        ("    6.3 Passive Tools", "17"),
        ("    6.4 Case Management and Entity Correlation", "18"),
        ("    6.5 PDF Report Generation", "18"),
        ("", ""),
        ("Chapter 7: Testing", "19"),
        ("Chapter 8: Results and Discussion", "20"),
        ("Chapter 9: Conclusion and Future Scope", "21"),
        ("References", "22"),
    ]
    for entry, page in toc_entries:
        p = doc.add_paragraph()
        p.paragraph_format.tab_stops.add_tab_stop(Inches(6.0),
            alignment=WD_ALIGN_PARAGRAPH.RIGHT, leader=2)
        p.paragraph_format.line_spacing = 1.3
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run(entry)
        run.font.size = Pt(12)
        run.font.name = "Times New Roman"
        if entry.startswith("Chapter"):
            run.font.bold = True
        if entry:
            p.add_run("\t").font.name = "Times New Roman"
            run2 = p.add_run(page)
            run2.font.size = Pt(12)
            run2.font.name = "Times New Roman"


# ========================================================================
#                          CHAPTERS
# ========================================================================

def build_chapter_1(doc):
    add_heading1(doc, "CHAPTER 1: INTRODUCTION")

    add_heading2(doc, "1.1 Overview")
    add_body(doc,
        "The rapid expansion of the internet, social media, and cloud "
        "services has transformed the way individuals and organizations "
        "interact with the digital world. Every online action, whether "
        "posting a photograph on a social network, registering a domain, "
        "or filing a corporate document with a public registry, leaves "
        "behind a small but permanent trace. Collectively, these traces "
        "form what is known as a digital footprint. Analyzing this "
        "footprint is a foundational activity in modern cybersecurity, "
        "digital forensics, journalism, and law enforcement.")

    add_body(doc,
        "The discipline concerned with the systematic collection and "
        "analysis of publicly available information is called Open "
        "Source Intelligence, commonly abbreviated as OSINT. OSINT "
        "practitioners investigate email addresses, phone numbers, "
        "usernames, IP addresses, domains, and photographs, correlating "
        "the resulting evidence to build a coherent picture of a target "
        "person, organization, or infrastructure.")

    add_body(doc,
        "Despite the importance of OSINT in the modern security "
        "landscape, the tools available to investigators are highly "
        "fragmented. A single investigation may require the use of ten "
        "or more different command-line utilities, each with its own "
        "input format, output format, and quirks. This fragmentation "
        "creates cognitive overhead, slows investigations, and makes "
        "the correlation of findings across tools a manual, error-prone "
        "process.")

    add_body(doc,
        "The Digital Footprint Investigator project addresses this "
        "problem by providing a single, unified web application that "
        "integrates 22 different OSINT tools under one clean, modern "
        "user interface. The system automates entity extraction, "
        "correlates findings across tools, and produces professional "
        "PDF investigation reports with a single click. The remainder "
        "of this chapter presents the motivation, problem statement, "
        "objectives, and scope of the project.")

    add_heading2(doc, "1.2 Motivation")
    add_body(doc,
        "The motivation for building the Digital Footprint Investigator "
        "arose from three principal observations made during personal "
        "study of cybersecurity and OSINT methodology.")

    add_body(doc,
        "First, established professional OSINT tools such as Maltego, "
        "SpiderFoot, and Recon-ng are powerful but present a steep "
        "learning curve. Their user interfaces are dense, and their "
        "output is often designed for expert users rather than "
        "beginners. There is a need for a simpler, more approachable "
        "toolkit that lowers the barrier to entry.")

    add_body(doc,
        "Second, popular open-source command-line tools such as "
        "Sherlock, theHarvester, and Nmap are excellent at their "
        "respective specialities but do not naturally interoperate. "
        "The output of one tool must be manually parsed and fed into "
        "the next. There is a clear need for a system that "
        "automatically correlates output across tools.")

    add_body(doc,
        "Third, generating a professional report at the end of an "
        "investigation currently requires manually collating outputs "
        "from many tools into a document editor. This process is "
        "tedious and inconsistent. An investigator would benefit "
        "greatly from a tool that automatically produces a coherent "
        "multi-page report suitable for submission to clients or "
        "supervisors.")

    add_heading2(doc, "1.3 Problem Statement")
    add_body(doc,
        "The problem addressed by this project can be stated as "
        "follows: to design and implement a unified OSINT toolkit that "
        "consolidates common reconnaissance and intelligence-gathering "
        "techniques under a single web interface, automatically "
        "correlates findings across tools, persists investigations for "
        "later review, and produces professional PDF reports for "
        "documentation and evidence purposes.")

    add_heading2(doc, "1.4 Objectives")
    add_body(doc, "The specific objectives of this project are:")
    add_bullets(doc, [
        "To design and implement a modern web-based user interface that "
        "clearly separates active reconnaissance tools from passive "
        "intelligence-gathering tools.",
        "To implement at least 20 distinct OSINT tools covering the "
        "full range of common investigation needs including domain, "
        "IP, email, phone, and username analysis.",
        "To provide configurable options for every tool, including "
        "basic and advanced modes to suit both novice and expert users.",
        "To automatically extract structured entities such as emails, "
        "IP addresses, subdomains, and GPS coordinates from every "
        "tool output and correlate them across an investigation.",
        "To persist all investigations in a lightweight local database "
        "so that findings survive application restarts.",
        "To generate professional multi-page PDF reports with a "
        "cryptographic integrity hash suitable for evidence submission.",
        "To provide a keyboard-driven command palette that allows "
        "power users to launch any tool or action with a few keystrokes.",
        "To package the entire system in a Docker container so that it "
        "can be deployed on any platform with a single command.",
    ])

    add_heading2(doc, "1.5 Scope of the Project")
    add_body(doc,
        "The scope of this project is limited to OSINT tools that "
        "operate on publicly available data sources or perform basic "
        "network reconnaissance against authorized targets. The system "
        "is intended for use in educational settings, authorized "
        "penetration testing engagements, and academic research. It is "
        "explicitly not intended for unauthorized access to systems, "
        "and appropriate warnings are included throughout the interface "
        "and documentation.")

    add_body(doc,
        "The project targets single-user or small-team usage. Multi-user "
        "authentication, role-based access control, and horizontal "
        "scaling to large user bases are out of scope for the current "
        "version but are identified as potential future enhancements.")

    add_heading2(doc, "1.6 Organization of the Report")
    add_body(doc,
        "This report is organized into nine chapters. Chapter 2 presents "
        "a literature review of existing OSINT tools and identifies the "
        "gap that this project aims to fill. Chapter 3 covers system "
        "analysis, including requirement analysis and feasibility "
        "studies. Chapter 4 details the system design, including "
        "architecture, database schema, and API design. Chapter 5 lists "
        "the technology stack in detail. Chapter 6 describes the "
        "implementation of each major component. Chapter 7 discusses "
        "the testing methodology. Chapter 8 presents results and "
        "discussion. Chapter 9 concludes the report and outlines "
        "future work.")


def build_chapter_2(doc):
    add_heading1(doc, "CHAPTER 2: LITERATURE REVIEW")

    add_heading2(doc, "2.1 Introduction to OSINT")
    add_body(doc,
        "Open Source Intelligence, or OSINT, is the practice of "
        "collecting and analyzing information from publicly available "
        "sources for intelligence purposes. The term was popularized "
        "by the United States military and intelligence community, "
        "although the underlying practice is far older and predates "
        "the digital era.")

    add_body(doc,
        "In the modern context, OSINT sources include social media "
        "platforms, news websites, blogs, forums, government publications, "
        "commercial databases, and technical records such as DNS, WHOIS, "
        "and Certificate Transparency logs. The value of OSINT lies not "
        "in individual data points, which are often trivial, but in the "
        "correlation of many small pieces of information into a coherent "
        "intelligence picture.")

    add_body(doc,
        "OSINT is broadly divided into two categories based on how the "
        "information is gathered. Passive OSINT involves collecting "
        "information from sources that do not require any direct "
        "interaction with the target, such as querying a WHOIS registry "
        "or searching a breach database. Active OSINT involves some "
        "form of direct interaction, such as scanning a target's open "
        "ports or crawling its website. The distinction is important "
        "because active techniques can be detected by the target and "
        "may have legal implications, whereas passive techniques are "
        "generally invisible and legally safer.")

    add_heading2(doc, "2.2 Existing Tools and Their Limitations")
    add_body(doc,
        "A survey of existing OSINT tools reveals a diverse and "
        "capable ecosystem, but one that suffers from significant "
        "usability limitations. The following tools were studied "
        "during the requirement analysis phase of this project.")

    add_heading3(doc, "2.2.1 Sherlock")
    add_body(doc,
        "Sherlock is an open-source Python tool that searches for a "
        "given username across hundreds of social networks. It is "
        "highly effective for its specific purpose but operates purely "
        "as a command-line utility. Its output is a plain text list of "
        "URLs with no correlation to other investigation data.")

    add_heading3(doc, "2.2.2 theHarvester")
    add_body(doc,
        "theHarvester is a command-line tool that gathers emails, "
        "subdomains, IP addresses, and other data from public sources "
        "such as search engines and PGP key servers. Like Sherlock, it "
        "is powerful in isolation but does not integrate with other "
        "tools in a common workflow.")

    add_heading3(doc, "2.2.3 Maltego")
    add_body(doc,
        "Maltego is a commercial graph-based intelligence platform "
        "that offers excellent visualization of relationships between "
        "entities. It is widely used by professional investigators, "
        "but its licensing cost, steep learning curve, and heavyweight "
        "desktop application make it unsuitable for casual or "
        "educational use.")

    add_heading3(doc, "2.2.4 SpiderFoot")
    add_body(doc,
        "SpiderFoot is a widely used open-source OSINT automation "
        "platform. It offers a web interface and correlates findings "
        "across many data sources. It is arguably the closest existing "
        "system to what this project aims to build. However, its user "
        "interface is dense and often overwhelming for beginners, and "
        "its report generation is limited to raw data exports rather "
        "than formatted PDF documents.")

    add_heading3(doc, "2.2.5 Nmap")
    add_body(doc,
        "Nmap is the industry-standard network scanning tool. It is "
        "extremely powerful and highly configurable, but it requires "
        "elevated system privileges for many of its scan types and "
        "presents its output in a format optimized for expert "
        "interpretation rather than beginner accessibility.")

    add_heading2(doc, "2.3 Research Gap")
    add_body(doc,
        "Based on the survey of existing tools, three clear gaps were "
        "identified. First, no existing tool combines the accessibility "
        "of a modern web interface with the breadth of coverage needed "
        "for practical investigations. Sherlock and theHarvester are "
        "narrow in scope; SpiderFoot is broad but presents a poor user "
        "experience for newcomers; Maltego is expensive and heavyweight.")

    add_body(doc,
        "Second, none of the surveyed tools automatically generates a "
        "professional PDF report suitable for evidence submission. "
        "Producing such a report currently requires manual work in an "
        "external editor.")

    add_body(doc,
        "Third, the correlation of findings across tools, though "
        "attempted by SpiderFoot and Maltego, is either overly complex "
        "for beginners or hidden behind expensive licensing. A simple, "
        "chip-based suggestion system that guides a novice investigator "
        "to the next logical tool would fill a real usability gap.")

    add_body(doc,
        "The Digital Footprint Investigator project targets exactly "
        "these three gaps: a modern accessible interface, professional "
        "PDF reporting, and lightweight but effective entity "
        "correlation with tool suggestions.")


def build_chapter_3(doc):
    add_heading1(doc, "CHAPTER 3: SYSTEM ANALYSIS")

    add_heading2(doc, "3.1 Requirement Analysis")

    add_heading3(doc, "3.1.1 Functional Requirements")
    add_body(doc,
        "The following functional requirements were identified for the "
        "system:")
    add_bullets(doc, [
        "The system shall provide a web-based user interface accessible "
        "from any modern browser.",
        "The system shall organize tools into two clearly distinguishable "
        "categories: active reconnaissance and passive intelligence.",
        "The system shall provide at least 20 OSINT tools covering "
        "domain, IP, email, phone, username, and file-based analysis.",
        "Every tool shall accept a target input and optional configuration "
        "parameters, and shall return a structured result.",
        "The system shall group tool runs under investigation cases and "
        "persist them across application restarts.",
        "The system shall automatically extract structured entities from "
        "each tool result and store them in a searchable database.",
        "The system shall suggest relevant next tools to the user based "
        "on the entities discovered in the current case.",
        "The system shall generate a professional multi-page PDF report "
        "for any case on demand.",
        "The system shall provide a keyboard-driven command palette "
        "accessible via the shortcut Ctrl+K.",
        "The system shall provide dark and light theme modes with "
        "user preference persistence.",
    ])

    add_heading3(doc, "3.1.2 Non-Functional Requirements")
    add_bullets(doc, [
        "Performance: Simple tools such as WHOIS lookup shall return "
        "results within five seconds. Complex tools such as port scans "
        "on 1000 ports shall complete within 60 seconds.",
        "Usability: The interface shall be usable by someone with no "
        "prior training in OSINT within 10 minutes.",
        "Portability: The system shall run on Windows, macOS, and Linux "
        "without modification.",
        "Deployability: The system shall be deployable via a single "
        "command using Docker.",
        "Security: API keys for third-party services shall be stored "
        "locally and shall never be transmitted to any party other than "
        "the intended service.",
        "Reliability: A failure in one tool shall not affect the "
        "availability of other tools.",
        "Maintainability: Each tool shall be implemented as an "
        "independent module to permit easy addition or removal of "
        "tools.",
    ])

    add_heading2(doc, "3.2 Feasibility Study")

    add_heading3(doc, "3.2.1 Technical Feasibility")
    add_body(doc,
        "All required functionality can be implemented using freely "
        "available, mature open-source libraries. Python provides an "
        "exceptional ecosystem of OSINT-related libraries including "
        "dnspython, python-whois, phonenumbers, Pillow, and reportlab. "
        "The Flask microframework offers a lightweight and well-documented "
        "path to building the HTTP API layer. Modern browsers provide "
        "sufficient JavaScript, CSS, and DOM capabilities to build the "
        "user interface without any build tools or frameworks. The "
        "project is therefore technically feasible.")

    add_heading3(doc, "3.2.2 Operational Feasibility")
    add_body(doc,
        "The system is designed for single-user operation on a personal "
        "computer or small-team deployment on an internal server. It "
        "requires no specialized hardware, no ongoing external service "
        "subscriptions for core functionality, and no complex operational "
        "procedures. Installation and startup are automated via Docker. "
        "The system is therefore operationally feasible.")

    add_heading3(doc, "3.2.3 Economic Feasibility")
    add_body(doc,
        "The project has zero direct financial cost. All software "
        "dependencies are open source and freely available. Optional "
        "third-party APIs such as HaveIBeenPwned and Shodan offer free "
        "tiers sufficient for personal and educational use. The system "
        "runs on commodity hardware and does not require cloud hosting "
        "for its core operation. The project is therefore economically "
        "feasible.")

    add_heading2(doc, "3.3 System Requirements")

    add_heading3(doc, "3.3.1 Hardware Requirements")
    add_table(doc, ["Component", "Minimum", "Recommended"], [
        ["Processor", "Dual-core 1.5 GHz", "Quad-core 2.5 GHz or better"],
        ["RAM", "2 GB", "4 GB or more"],
        ["Disk space", "500 MB", "2 GB (includes room for cases)"],
        ["Network", "Broadband Internet", "Broadband Internet"],
    ], col_widths=[2.0, 2.0, 2.5])

    add_heading3(doc, "3.3.2 Software Requirements")
    add_table(doc, ["Component", "Version"], [
        ["Operating System", "Windows 10/11, macOS 12+, or any modern Linux"],
        ["Python", "3.10 or later"],
        ["Web browser", "Chrome, Firefox, Edge (any recent version)"],
        ["Docker (optional)", "20.10 or later, with Compose plugin"],
    ], col_widths=[2.5, 4.0])


def build_chapter_4(doc):
    add_heading1(doc, "CHAPTER 4: SYSTEM DESIGN")

    add_heading2(doc, "4.1 Architectural Overview")
    add_body(doc,
        "The system follows a classic three-tier architecture consisting "
        "of a presentation layer, an application layer, and a data "
        "layer. The presentation layer is a static single-page web "
        "application delivered to the user's browser. The application "
        "layer is a Python Flask server that exposes a JSON REST API "
        "and hosts the 22 tool modules. The data layer is a local SQLite "
        "database file that stores investigation cases, results, and "
        "extracted entities.")

    add_figure_placeholder(doc, "High-level system architecture")

    add_body(doc,
        "Communication between the browser and the Flask server is "
        "performed exclusively over HTTP with JSON payloads. This clean "
        "separation means that the backend could later serve additional "
        "clients such as a command-line interface or a mobile "
        "application without any changes.")

    add_body(doc,
        "Within the application layer, the code is organized into "
        "clearly separated concerns. The tool modules under backend/tools "
        "each implement a single OSINT tool with a uniform run() "
        "function signature. The correlation module extracts entities "
        "from tool outputs and drives the next-tool suggestion engine. "
        "The report_generator module produces the PDF output. The db "
        "module encapsulates all SQLite interactions.")

    add_heading2(doc, "4.2 Database Design")
    add_body(doc,
        "The database uses three tables in a straightforward relational "
        "schema. The cases table stores metadata about each investigation. "
        "The results table stores every tool invocation with its output "
        "and status, linked to a case by a foreign key. The entities "
        "table stores structured facts extracted from tool outputs, "
        "linked to both a case and a source result. Foreign key "
        "cascades ensure that deleting a case removes all associated "
        "records automatically.")

    add_figure_placeholder(doc, "Database schema (ER diagram)")

    add_body(doc, "The schema definition is shown below.")
    add_code_block(doc, """
CREATE TABLE cases (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    primary_target TEXT,
    description    TEXT DEFAULT '',
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);

CREATE TABLE results (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id        INTEGER NOT NULL,
    tool_id        TEXT NOT NULL,
    tool_name      TEXT NOT NULL,
    tool_type      TEXT NOT NULL,
    target         TEXT NOT NULL,
    options_json   TEXT DEFAULT '{}',
    status         TEXT NOT NULL,
    result_json    TEXT,
    error          TEXT,
    started_at     TEXT NOT NULL,
    finished_at    TEXT,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
);

CREATE TABLE entities (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id          INTEGER NOT NULL,
    entity_type      TEXT NOT NULL,
    value            TEXT NOT NULL,
    source_tool_id   TEXT,
    source_result_id INTEGER,
    first_seen       TEXT NOT NULL,
    UNIQUE(case_id, entity_type, value),
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
);
""")

    add_body(doc,
        "SQLite's Write-Ahead Logging mode is enabled to allow concurrent "
        "reads while a write is in progress, which improves performance "
        "under the multi-threaded Flask server.")

    add_heading2(doc, "4.3 API Design")
    add_body(doc,
        "The Flask backend exposes a clean REST API. The main endpoints "
        "are summarized in the table below.")

    add_table(doc, ["Method", "Endpoint", "Purpose"], [
        ["GET",  "/api/health", "Health check for monitoring."],
        ["POST", "/api/run/<tool_id>", "Execute a tool with optional case ID."],
        ["GET",  "/api/cases", "List all investigation cases."],
        ["POST", "/api/cases", "Create a new case."],
        ["GET",  "/api/cases/<id>", "Fetch a case with all results and entities."],
        ["PATCH","/api/cases/<id>", "Rename or update a case."],
        ["DELETE","/api/cases/<id>", "Delete a case and all its data."],
        ["GET",  "/api/cases/<id>/report.pdf", "Generate PDF report for a case."],
        ["GET",  "/api/cases/<id>/suggestions", "Get next-tool suggestions."],
        ["GET",  "/api/auth/status", "Check API key configuration."],
        ["POST", "/api/auth/update", "Update an external service API key."],
    ], col_widths=[0.8, 2.5, 3.2])

    add_heading2(doc, "4.4 User Interface Design")
    add_body(doc,
        "The user interface is designed around three tab panels. The "
        "Active panel groups the eight tools that interact directly with "
        "a target. The Passive panel groups the fourteen tools that use "
        "only publicly available data. The Results panel presents the "
        "history of the currently selected investigation case with "
        "expandable result cards, entity chips, and suggestion pills.")

    add_body(doc,
        "The header includes three interactive elements: a case selector "
        "pill that opens the case manager modal, a command palette "
        "trigger, and a dark/light theme toggle. A dedicated command "
        "palette accessible via Ctrl+K allows expert users to launch any "
        "tool or action using fuzzy search and keyboard navigation.")

    add_figure_placeholder(doc, "Screenshot of the main user interface")


def build_chapter_5(doc):
    add_heading1(doc, "CHAPTER 5: TECHNOLOGY STACK")

    add_body(doc,
        "The technology stack was chosen to balance capability, "
        "maturity, developer productivity, and ease of deployment. "
        "Every component is free and open-source, and all combined "
        "have a large developer community.")

    add_heading2(doc, "5.1 Backend Technologies")
    add_table(doc, ["Technology", "Purpose"], [
        ["Python 3.12", "Primary programming language for the backend."],
        ["Flask 3.0", "Lightweight web framework for the REST API."],
        ["Flask-CORS", "Cross-Origin Resource Sharing support."],
        ["SQLite 3", "Embedded relational database."],
        ["ReportLab 4.2", "PDF report generation library."],
        ["Gunicorn", "Production-grade WSGI server used in Docker."],
    ], col_widths=[2.0, 4.5])

    add_heading2(doc, "5.2 OSINT-Specific Libraries")
    add_table(doc, ["Library", "Purpose"], [
        ["dnspython", "DNS record queries including AXFR and DNSSEC."],
        ["python-whois", "WHOIS registry lookups."],
        ["phonenumbers", "Parsing and analysis of international phone numbers."],
        ["Pillow (PIL)", "Image processing and EXIF metadata extraction."],
        ["PyPDF2", "PDF metadata and text extraction."],
        ["BeautifulSoup4", "HTML parsing for the crawler and website analyzer."],
        ["requests", "HTTP client for all outgoing web requests."],
    ], col_widths=[2.0, 4.5])

    add_heading2(doc, "5.3 Frontend Technologies")
    add_table(doc, ["Technology", "Purpose"], [
        ["HTML5", "Structure of the user interface."],
        ["CSS3", "Styling, including custom properties for theming."],
        ["Vanilla JavaScript (ES2020)", "Interactivity, API calls, and state."],
        ["Fetch API", "Asynchronous HTTP calls from the browser."],
        ["localStorage", "Persistence of theme and case selection."],
    ], col_widths=[2.5, 4.0])

    add_heading2(doc, "5.4 Deployment and Tooling")
    add_table(doc, ["Technology", "Purpose"], [
        ["Docker", "Containerization for portable deployment."],
        ["Docker Compose", "One-command orchestration."],
        ["Git", "Version control."],
        ["GitHub", "Repository hosting and pull request workflow."],
    ], col_widths=[2.0, 4.5])


def build_chapter_6(doc):
    add_heading1(doc, "CHAPTER 6: IMPLEMENTATION")

    add_heading2(doc, "6.1 Project Structure")
    add_body(doc,
        "The project is organized into a clear directory structure "
        "that separates the frontend, backend, and tool modules.")
    add_code_block(doc, """
Digital-Footprint-Investigator/
|-- index.html               # Single-page frontend
|-- style.css
|-- script.js
|-- backend/
|   |-- app.py               # Flask application and routes
|   |-- db.py                # SQLite persistence layer
|   |-- correlation.py       # Entity extraction and suggestions
|   |-- report_generator.py  # PDF report builder
|   |-- config.py            # API key storage
|   |-- data/                # Runtime data (DB, keys)
|   |-- requirements.txt
|   `-- tools/               # 22 tool modules
|       |-- port_scan.py
|       |-- dns_enum.py
|       |-- ... (20 more)
|-- Dockerfile
|-- docker-compose.yml
`-- README.md
""")

    add_heading2(doc, "6.2 Active Tools")

    add_heading3(doc, "6.2.1 Port Scanning")
    add_body(doc,
        "The port scanner uses Python's built-in socket module to "
        "perform TCP connect scans. A ThreadPoolExecutor with up to "
        "200 workers concurrently probes ports on the target host. "
        "Users can choose from four modes: basic (35 common ports), "
        "advanced (top 1000 ports), full (all 65,535 ports), or a "
        "custom range specified as a comma-separated list. An optional "
        "banner-grabbing feature attempts to read the first bytes of "
        "each open service to identify the software behind it.")

    add_heading3(doc, "6.2.2 DNS Enumeration")
    add_body(doc,
        "DNS enumeration is built on the dnspython library. In basic "
        "mode, the tool queries seven standard record types: A, AAAA, "
        "MX, NS, TXT, CNAME, and SOA. In advanced mode, the tool also "
        "queries CAA, DNSKEY, and DS records, attempts an AXFR zone "
        "transfer against every authoritative name server, and extracts "
        "SPF and DMARC email authentication policies from TXT records.")

    add_heading3(doc, "6.2.3 Subdomain Enumeration")
    add_body(doc,
        "Subdomain discovery is performed against Certificate Transparency "
        "logs via the crt.sh public API. Because every SSL certificate "
        "issued by a public Certificate Authority is publicly logged, "
        "and because certificates typically enumerate all covered "
        "hostnames in the Subject Alternative Name extension, CT logs "
        "are an excellent source of subdomain discovery. In advanced "
        "mode, the tool also performs DNS brute-forcing against a "
        "curated wordlist of approximately 150 common subdomain "
        "prefixes.")

    add_heading3(doc, "6.2.4 WHOIS Lookup")
    add_body(doc,
        "The WHOIS module uses the python-whois library, which handles "
        "the many quirks of parsing WHOIS server responses across TLDs. "
        "It extracts registrar, creation and expiration dates, name "
        "servers, and administrative and technical contacts. Note that "
        "many modern registries, particularly those governed by GDPR, "
        "redact personal information in WHOIS responses.")

    add_heading3(doc, "6.2.5 Directory Brute-Force")
    add_body(doc,
        "The directory brute-force tool sends parallel HTTP HEAD "
        "requests to guess URL paths from a built-in wordlist. Three "
        "wordlist sizes are available: small (25 well-known paths), "
        "medium (approximately 130 paths), and large (approximately 250 "
        "paths including CI/CD-specific endpoints). An optional file "
        "extension setting appends common extensions such as php, bak, "
        "and old to each path.")

    add_heading3(doc, "6.2.6 Web Crawler")
    add_body(doc,
        "The web crawler performs a breadth-first crawl of the target "
        "website with configurable page and depth limits. It extracts "
        "internal and external links, HTML forms, and, when enabled, "
        "email addresses, phone numbers, and social media profile URLs "
        "from the HTML body. It respects robots.txt directives by "
        "default, in line with ethical crawling practice.")

    add_heading3(doc, "6.2.7 SSL/TLS Scanner")
    add_body(doc,
        "The SSL scanner uses Python's built-in ssl module to establish "
        "a TLS handshake with the target and extract the certificate "
        "chain, cipher suite, protocol version, and expiration date. "
        "The tool computes an A-plus through F letter grade based on "
        "TLS version support, cipher strength, self-signed status, and "
        "certificate expiry proximity, in a manner similar to the "
        "well-known SSL Labs test.")

    add_heading3(doc, "6.2.8 Banner Grabbing")
    add_body(doc,
        "Banner grabbing connects to specified TCP ports and reads the "
        "initial bytes of the service response. Signature matching "
        "then identifies common services such as SSH, FTP, SMTP, HTTP, "
        "MySQL, and Redis. This provides more reliable service "
        "identification than port-number-based inference.")

    add_heading2(doc, "6.3 Passive Tools")

    add_heading3(doc, "6.3.1 Username Lookup")
    add_body(doc,
        "The username lookup tool searches for a given username on more "
        "than 90 online platforms across seven categories: social media, "
        "developer platforms, gaming, creative arts, professional "
        "profiles, forums, and miscellaneous. Each check is an HTTP "
        "request to the platform's profile URL, and the tool identifies "
        "presence based on the returned HTTP status code or specific "
        "text patterns in the response body.")

    add_heading3(doc, "6.3.2 Email Investigation")
    add_body(doc,
        "Email investigation performs several checks in sequence: "
        "syntactic validation using a regular expression, MX record "
        "lookup to verify the domain can receive mail, comparison "
        "against a curated list of known disposable email providers, "
        "Gravatar profile lookup using the MD5 hash of the email "
        "address, breach detection via the HaveIBeenPwned API, and "
        "optional deeper verification using the Hunter.io service.")

    add_heading3(doc, "6.3.3 IP Investigation")
    add_body(doc,
        "IP investigation uses the ip-api.com service for free "
        "geolocation, ASN lookup, and hosting-provider identification. "
        "In advanced mode, the tool queries the Shodan API for open "
        "ports and known vulnerabilities, the AbuseIPDB service for "
        "abuse reports, and the VirusTotal service for reputation "
        "data.")

    add_heading3(doc, "6.3.4 Phone Investigation")
    add_body(doc,
        "Phone number analysis uses the phonenumbers library, a port "
        "of Google's libphonenumber to Python. The tool identifies "
        "country code, region, carrier, line type (mobile, fixed, "
        "VoIP), and associated timezones. It additionally generates "
        "search URLs for popular phone-lookup services such as "
        "TrueCaller, NumLookup, and BeenVerified.")

    add_heading3(doc, "6.3.5 Metadata Extraction")
    add_body(doc,
        "The metadata extractor supports both image and PDF files. "
        "Images are analyzed with Pillow to extract EXIF metadata, "
        "including camera information and, most importantly, embedded "
        "GPS coordinates. When GPS data is present, the tool converts "
        "the degrees-minutes-seconds representation to decimal degrees "
        "and generates clickable Google Maps and OpenStreetMap links. "
        "PDF files are analyzed with PyPDF2 to extract author, creation "
        "date, and, in full mode, a text preview of the first pages.")

    add_heading3(doc, "6.3.6 Website Analysis")
    add_body(doc,
        "The website analyzer fingerprints the technology stack of a "
        "target site by running approximately 60 regular expression "
        "signatures against the response body and headers. It audits "
        "security-related HTTP response headers, isolates third-party "
        "tracking scripts, parses robots.txt, and, in advanced mode, "
        "extracts URLs from the sitemap.xml file.")

    add_heading3(doc, "6.3.7 Data Breach Check")
    add_body(doc,
        "The breach check tool integrates with the HaveIBeenPwned "
        "service. For account lookup, it queries the paid HIBP API "
        "using the user's API key. For password checking, it uses the "
        "public Pwned Passwords API with the k-anonymity model: the "
        "tool computes SHA-1 of the password locally, sends only the "
        "first five hex characters of the hash to the API, and checks "
        "the returned list of hash suffixes locally. This ensures that "
        "the password itself never leaves the user's machine.")

    add_heading2(doc, "6.4 Case Management and Entity Correlation")
    add_body(doc,
        "Every successful tool run is automatically persisted under an "
        "investigation case. If the user has not selected a case, the "
        "system silently creates one and remembers the choice via "
        "localStorage. After each run, the correlation module extracts "
        "structured entities from the result: emails, IP addresses, "
        "domain names, subdomain names, usernames, phone numbers, URLs, "
        "GPS coordinates, open port descriptors, technology fingerprints, "
        "and CVE identifiers.")

    add_body(doc,
        "The suggestion engine then examines the set of entities in "
        "the current case and produces a ranked list of next tools to "
        "run. For example, if the email address alice@example.com is "
        "discovered, the engine suggests running Email Investigation "
        "and Breach Check on the address, as well as Username Lookup "
        "on the local part 'alice'. Suggestions are surfaced in the "
        "user interface as clickable chips that pre-fill the target "
        "field of the corresponding tool.")

    add_heading2(doc, "6.5 PDF Report Generation")
    add_body(doc,
        "PDF report generation is implemented using the ReportLab "
        "library. When the user requests a report for a case, the "
        "server assembles the case data, builds a multi-page A4 "
        "document with a branded cover page, an executive summary, an "
        "entity index grouped by type, and detailed per-tool findings "
        "produced by 14 specialized renderers, and computes a SHA-256 "
        "hash of the final PDF for chain-of-custody purposes. The hash "
        "is returned in the X-Report-SHA256 HTTP header and can be "
        "used to verify the integrity of the report.")


def build_chapter_7(doc):
    add_heading1(doc, "CHAPTER 7: TESTING")

    add_heading2(doc, "7.1 Testing Approach")
    add_body(doc,
        "The system was tested using a combination of manual functional "
        "testing, integration testing across the frontend and backend, "
        "and syntax verification using Python's built-in py_compile "
        "module. Given the interactive, exploratory nature of an OSINT "
        "toolkit, manual testing was found to be more informative than "
        "automated testing at this stage of the project.")

    add_heading2(doc, "7.2 Test Cases")
    add_body(doc,
        "Each of the 22 tools was tested against publicly authorized "
        "targets. The following table summarizes representative test "
        "cases.")

    add_table(doc, ["Tool", "Test Target", "Expected", "Result"], [
        ["Port Scan", "scanme.nmap.org", "Discover ports 22 and 80", "Pass"],
        ["DNS Enum", "google.com", "A, MX, NS, TXT records returned", "Pass"],
        ["Subdomain Enum", "github.com", "Multiple subdomains listed", "Pass"],
        ["WHOIS", "example.com", "Registrar, dates, and IANA records", "Pass"],
        ["Dir Brute", "http://scanme.nmap.org", "Standard paths detected", "Pass"],
        ["SSL Scan", "github.com", "Grade A or higher, TLS 1.3", "Pass"],
        ["Username Lookup", "torvalds", "Match on GitHub, StackOverflow", "Pass"],
        ["Email Investigation", "test@gmail.com", "MX found, free provider flagged", "Pass"],
        ["IP Investigation", "8.8.8.8", "Geolocation returns Google DNS", "Pass"],
        ["Phone Investigation", "+1 202-456-1414", "Country US, carrier known", "Pass"],
        ["Website Analysis", "https://github.com", "Detects Nginx, React, GitHub tech", "Pass"],
        ["Breach Check", "password123", "Reports millions of breaches", "Pass"],
        ["PDF Report", "any case", "Downloadable PDF with hash header", "Pass"],
        ["Command Palette", "Ctrl+K", "Palette opens, fuzzy search works", "Pass"],
    ], col_widths=[1.5, 1.7, 2.0, 0.8])

    add_heading2(doc, "7.3 Observations")
    add_body(doc,
        "During testing, three noteworthy issues were identified and "
        "resolved. First, the crt.sh subdomain enumeration API can be "
        "rate-limited under heavy use, and the tool now handles JSON "
        "parse failures gracefully. Second, WHOIS responses for some "
        "TLDs return no useful data due to GDPR redaction, and the tool "
        "reports this clearly rather than failing silently. Third, "
        "several username-lookup platforms return HTTP 200 for missing "
        "users, requiring body-text matching rather than status-only "
        "checks.")


def build_chapter_8(doc):
    add_heading1(doc, "CHAPTER 8: RESULTS AND DISCUSSION")

    add_body(doc,
        "The final system meets all of the functional and non-functional "
        "requirements defined in Chapter 3. All 22 tools operate "
        "correctly against publicly authorized targets. Investigation "
        "cases persist across restarts. Entity correlation reliably "
        "extracts structured facts from tool outputs, and the suggestion "
        "engine consistently proposes relevant next tools. PDF reports "
        "are produced within a few seconds for cases of moderate size.")

    add_figure_placeholder(doc, "Screenshot of case with results and suggestions")

    add_figure_placeholder(doc, "Screenshot of generated PDF report cover page")

    add_body(doc,
        "The command palette has proven particularly valuable in "
        "day-to-day use, reducing the time to launch a specific tool "
        "from a few clicks to a two- or three-keystroke fuzzy search. "
        "Similarly, the dark and light theme toggle has been well "
        "received during demonstrations, as it accommodates a wide "
        "range of lighting environments and personal preferences.")

    add_body(doc,
        "Compared to existing tools surveyed in Chapter 2, the Digital "
        "Footprint Investigator offers a substantially better beginner "
        "experience while retaining the breadth of coverage typically "
        "associated with more advanced platforms. It compares favorably "
        "against Sherlock in coverage, against theHarvester in "
        "interactive experience, against SpiderFoot in ease of use, "
        "and against Maltego in accessibility and cost.")

    add_body(doc,
        "The system's Docker packaging has also proven to be an "
        "important practical asset. A single docker compose up command "
        "brings the entire application online, greatly reducing the "
        "friction of trying out the tool on a new machine.")


def build_chapter_9(doc):
    add_heading1(doc, "CHAPTER 9: CONCLUSION AND FUTURE SCOPE")

    add_heading2(doc, "9.1 Conclusion")
    add_body(doc,
        "This project set out to build a unified OSINT toolkit that "
        "consolidates common reconnaissance and intelligence-gathering "
        "techniques under a single, approachable interface. The "
        "resulting system, Digital Footprint Investigator, integrates "
        "22 distinct tools, persists investigations in a lightweight "
        "SQLite database, automatically correlates findings across "
        "tools, generates professional PDF reports with cryptographic "
        "integrity hashing, and can be deployed with a single Docker "
        "Compose command.")

    add_body(doc,
        "The project has successfully demonstrated that a well-designed "
        "web application can bridge the gap between the powerful but "
        "fragmented command-line OSINT ecosystem and the heavyweight "
        "commercial platforms that dominate professional practice. It "
        "has also demonstrated the practical value of small design "
        "features such as a command palette, an entity-driven "
        "suggestion engine, and a theme toggle in a real security "
        "tool.")

    add_body(doc,
        "In the course of building the project, the author has gained "
        "substantial experience with Python web development, database "
        "design, cryptographic hashing, cross-language integration, "
        "and modern frontend techniques. The project also afforded "
        "the opportunity to study OSINT methodology in depth and to "
        "read broadly on internet infrastructure topics such as "
        "Certificate Transparency, DNS security extensions, and "
        "cryptographic privacy techniques such as k-anonymity.")

    add_heading2(doc, "9.2 Future Scope")
    add_body(doc,
        "Several enhancements are planned for future versions of the "
        "system. The most impactful of these are described below.")

    add_bullets(doc, [
        "Multi-user authentication with role-based access control, "
        "enabling teams of investigators to share cases and collaborate "
        "on complex investigations.",
        "A background job queue based on Celery and Redis, allowing "
        "long-running scans to execute without blocking the user "
        "interface and enabling scheduled or recurring investigations.",
        "An entity relationship graph visualization using D3.js or "
        "Cytoscape, allowing investigators to see connections between "
        "emails, IPs, domains, and other entities visually.",
        "Machine learning-based anomaly detection to flag unusual "
        "patterns in target activity or infrastructure.",
        "Integration with commercial threat intelligence feeds such as "
        "MISP, AlienVault OTX, and PhishTank for enriched risk scoring.",
        "A REST API with OpenAPI documentation and API keys for "
        "external integrations, enabling programmatic use of the "
        "system from scripts and other applications.",
        "A native mobile application (Android and iOS) for on-the-go "
        "investigators.",
        "A plugin system that allows community members to contribute "
        "additional tools without modifying the core codebase.",
    ])


def build_references(doc):
    add_heading1(doc, "REFERENCES")
    refs = [
        "Bazzell, M. (2024). Open Source Intelligence Techniques: "
        "Resources for Searching and Analyzing Online Information. "
        "9th ed. IntelTechniques Publishing.",

        "The Sherlock Project. (2024). Sherlock: Hunt down social media "
        "accounts by username. GitHub repository. "
        "https://github.com/sherlock-project/sherlock",

        "Grinberg, M. (2018). Flask Web Development: Developing Web "
        "Applications with Python. 2nd ed. O'Reilly Media.",

        "Nawrocki, M., et al. (2020). Certificate Transparency in the "
        "Wild. Proceedings of the ACM Internet Measurement Conference.",

        "SQLite Consortium. (2024). SQLite Documentation. "
        "https://www.sqlite.org/docs.html",

        "Python Software Foundation. (2024). Python 3 Standard Library "
        "Documentation. https://docs.python.org/3/",

        "OWASP Foundation. (2024). OWASP Testing Guide v4.2. "
        "https://owasp.org/www-project-web-security-testing-guide/",

        "Have I Been Pwned. (2024). Pwned Passwords API v3. "
        "https://haveibeenpwned.com/API/v3",

        "Google Inc. (2024). libphonenumber: Google's phone number "
        "handling library. GitHub. "
        "https://github.com/google/libphonenumber",

        "ReportLab Inc. (2024). ReportLab PDF Toolkit Documentation. "
        "https://www.reportlab.com/documentation/",

        "Lyon, G. (2009). Nmap Network Scanning: The Official Nmap "
        "Project Guide to Network Discovery and Security Scanning. "
        "Nmap Project.",

        "Docker Inc. (2024). Docker Documentation. "
        "https://docs.docker.com/",

        "MDN Web Docs. (2024). Web APIs Reference. Mozilla Foundation. "
        "https://developer.mozilla.org/en-US/docs/Web/API",
    ]
    for i, r in enumerate(refs, start=1):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.4)
        p.paragraph_format.first_line_indent = Inches(-0.4)
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(8)
        run = p.add_run(f"[{i}]  ")
        run.font.name = "Times New Roman"
        run.font.size = Pt(12)
        run.font.bold = True
        run2 = p.add_run(r)
        run2.font.name = "Times New Roman"
        run2.font.size = Pt(12)


# ========================================================================
#                            BUILD
# ========================================================================

def build():
    doc = Document()

    set_default_font(doc)
    set_margins(doc)
    add_page_number(doc)

    # Front matter
    build_cover_page(doc)
    build_certificate(doc)
    build_declaration(doc)
    build_acknowledgment(doc)
    build_abstract(doc)
    build_toc(doc)

    # Main chapters
    build_chapter_1(doc)
    build_chapter_2(doc)
    build_chapter_3(doc)
    build_chapter_4(doc)
    build_chapter_5(doc)
    build_chapter_6(doc)
    build_chapter_7(doc)
    build_chapter_8(doc)
    build_chapter_9(doc)
    build_references(doc)

    doc.save(OUTPUT)
    print(f"[OK] Saved {OUTPUT}")
    print(f"    Approximate page count: 20-22")


if __name__ == "__main__":
    build()
