"""Build one shared Floodline guide as Markdown, editable Word and a Word-rendered PDF.

Run: python outputs/_build/user_guide/build_user_guide.py
Requires python-docx, Pillow and PyMuPDF; PDF export uses installed Microsoft Word
through pywin32 on Windows. Use --skip-pdf to omit Word automation.
The screen capture script is separate so rebuilding prose never changes app data.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from PIL import Image, ImageDraw, ImageFont

from guide_content import DATE, PAGES, SUBTITLE, TITLE, VERSION


ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "outputs"
ASSETS = ROOT / "docs" / "user-guide" / "images"
DISPLAY = ASSETS / "display"
QA = OUTPUT / "_qa" / "user-guide"
DOCX = OUTPUT / "Floodline_User_Guide.docx"
PDF = OUTPUT / "Floodline_User_Guide.pdf"
MARKDOWN = ROOT / "docs" / "USER_GUIDE.md"
INK = "203741"
TEAL = "087F82"
MUTED = "506771"
PALE = "EAF3F2"
LINE = "D6E3E6"
PAGE_WIDTH = 501.28

LABELS = sorted([
    "Rule and source details", "Verified community reports", "Report waterlogging",
    "Area subscriptions", "Delivery history", "Refresh history", "Refresh queue",
    "Observation location", "Submit for review", "Save correction", "Withdraw evidence",
    "Withdraw report", "Keep report", "New report", "Your reports", "Passage conditions",
    "Observed at", "From", "To", "Find route", "Swap direction", "Inspect route segments",
    "Moderator sign in", "Return to resident", "Pending", "Verified", "Review reason",
    "Verify observation", "Reject evidence", "Mark as duplicate", "Affected mapped segment",
    "Verify report", "Record resolution", "Resolve verified hazard", "Recent audit trail",
    "Light rain", "Heavy rain", "Feed outage", "Recover feed", "Process again",
    "Fail next delivery", "Data & model", "Evidence review", "Route suggestions",
    "Your alerts", "Flood map", "Reports", "Study area", "Area evidence", "Data support",
    "Risk cells", "OSM map", "Rainfall history", "Observed waterlogging", "Appearance",
    "Subscribe", "System", "Light", "Dark", "Demo time", "Valid to", "Issued"
], key=len, reverse=True)
LABEL_PATTERN = re.compile(r"(?<!\w)(" + "|".join(re.escape(x) for x in LABELS) + r")(?!\w)")


def rgb(hex_color):
    return RGBColor.from_string(hex_color)


def font(size, bold=False):
    return ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf", size)


def prepare_assets():
    DISPLAY.mkdir(parents=True, exist_ok=True)
    crops = {
        "01-flood-map": (244, 172, 1410, 810),
        "03-dark-map": (244, 172, 1410, 810),
        "06-route-found": (244, 65, 1410, 820),
        "07-report-form": (244, 172, 1410, 880),
        "08-pending-report": (244, 65, 1410, 575),
        "09-alerts": (244, 140, 1410, 671),
        "10-data-model": (244, 65, 1410, 845),
        "12-evidence-review": (244, 218, 1410, 835),
        "14-route-after-review": (244, 135, 1410, 820),
        "16-feed-outage": (244, 65, 1410, 810),
    }
    names = {b["name"] for page in PAGES for b in page["blocks"] if b["kind"] == "figure"}
    for name in names | {"03-dark-map"}:
        if name in ("navigation-pair", "data-flow"):
            continue
        source = ASSETS / f"{name}.png"
        image = Image.open(source).convert("RGB")
        if name in crops:
            image = image.crop(crops[name])
        image.save(DISPLAY / f"{name}.png", optimize=True)

    # Keep actual interface pixels; compose desktop controls and a phone menu.
    sidebar = Image.open(ASSETS / "01-flood-map.png").convert("RGB")
    mobile = Image.open(ASSETS / "04-mobile-navigation.png").convert("RGB")
    composite = Image.new("RGB", (1030, 700), "#F5F8F9")
    draw = ImageDraw.Draw(composite)
    draw.text((35, 20), "DESKTOP", font=font(21, True), fill="#203741")
    draw.text((520, 20), "MOBILE NAVIGATION", font=font(21, True), fill="#203741")
    nav = sidebar.crop((10, 181, 216, 468)).resize((371, 517), Image.Resampling.LANCZOS)
    appearance = sidebar.crop((12, 844, 211, 896)).resize((358, 94), Image.Resampling.LANCZOS)
    composite.paste(nav, (35, 58))
    composite.paste(appearance, (35, 584))
    phone = mobile.resize((291, 630), Image.Resampling.LANCZOS)
    composite.paste(phone, (580, 58))
    composite.save(DISPLAY / "navigation-pair.png", optimize=True)

    # A code-rendered architecture diagram, independent of the app UI.
    flow = Image.new("RGB", (1280, 428), "#FFFFFF")
    draw = ImageDraw.Draw(flow)
    def box(x, y, width, title, secondary, color="#EAF3F2"):
        draw.rounded_rectangle((x, y, x + width, y + 85), radius=11, fill=color, outline="#CDDDE0", width=2)
        draw.text((x + 15, y + 15), title, font=font(20, True), fill="#203741")
        draw.text((x + 15, y + 47), secondary, font=font(18), fill="#506771")
    def arrow(x1, y, x2):
        draw.line((x1, y, x2, y), fill="#087F82", width=4)
        draw.polygon([(x2, y), (x2 - 10, y - 7), (x2 - 10, y + 7)], fill="#087F82")
    environment = [("Synthetic inputs", "Rainfall + gauges"), ("Validate records", "Units + duplicates"),
                   ("Features + GIS", "Receipt-time data"), ("Relative rule", "Demo thresholds"),
                   ("Map + ward alerts", "Evidence + validity")]
    for i, (title, secondary) in enumerate(environment):
        x = 12 + i * 254
        box(x, 24, 235, title, secondary)
        if i < 4:
            arrow(x + 237, 66, x + 252)
    report_stream = [("Resident evidence", "Text + optional image"), ("Private review", "Time, place + privacy"),
                     ("Verified restriction", "Matched road edges"), ("Map, routes + alerts", "Separate action stream")]
    for i, (title, secondary) in enumerate(report_stream):
        x = 12 + i * 320
        box(x, 163, 298, title, secondary, "#EFF3F7")
        if i < 3:
            arrow(x + 300, 205, x + 318)
    draw.line((12, 289, 1260, 289), fill="#D6E3E6", width=2)
    draw.text((12, 310), "SEPARATE EVALUATION", font=font(17, True), fill="#506771")
    draw.text((12, 346), "Event ledger  →  chronological experiment  →  unpromoted model artifact",
              font=font(25), fill="#203741")
    draw.text((12, 391), "The experiment is not connected to the running map's decision path.",
              font=font(19), fill="#506771")
    flow.save(DISPLAY / "data-flow.png", optimize=True)


def rich(paragraph, text, size=None, color=None, bold=False):
    cursor = 0
    matches = list(LABEL_PATTERN.finditer(text)) if not bold else []
    for match in matches:
        if match.start() > cursor:
            run = paragraph.add_run(text[cursor:match.start()])
            if size: run.font.size = Pt(size)
            if color: run.font.color.rgb = rgb(color)
        run = paragraph.add_run(match.group())
        run.bold = True
        if size: run.font.size = Pt(size)
        if color: run.font.color.rgb = rgb(color)
        cursor = match.end()
    if cursor < len(text) or not text:
        run = paragraph.add_run(text[cursor:])
        run.bold = bold
        if size: run.font.size = Pt(size)
        if color: run.font.color.rgb = rgb(color)
    return paragraph


def xml_border(parent, tag, color=LINE, size="4"):
    element = OxmlElement(tag)
    element.set(qn("w:val"), "single")
    element.set(qn("w:sz"), size)
    element.set(qn("w:color"), color)
    parent.append(element)


def shade(cell, fill):
    element = OxmlElement("w:shd")
    element.set(qn("w:fill"), fill)
    cell._tc.get_or_add_tcPr().append(element)


def cell_margins(cell, top=75, bottom=75, left=95, right=95):
    element = OxmlElement("w:tcMar")
    for edge, value in (("top", top), ("bottom", bottom), ("left", left), ("right", right)):
        item = OxmlElement(f"w:{edge}")
        item.set(qn("w:w"), str(value))
        item.set(qn("w:type"), "dxa")
        element.append(item)
    cell._tc.get_or_add_tcPr().append(element)


def field(paragraph, instruction, fallback="1"):
    element = OxmlElement("w:fldSimple")
    element.set(qn("w:instr"), instruction)
    run = OxmlElement("w:r")
    content = OxmlElement("w:t")
    content.text = fallback
    run.append(content)
    element.append(run)
    paragraph._p.append(element)


def bookmark(paragraph, name, identifier):
    start = OxmlElement("w:bookmarkStart")
    start.set(qn("w:id"), str(identifier))
    start.set(qn("w:name"), name)
    end = OxmlElement("w:bookmarkEnd")
    end.set(qn("w:id"), str(identifier))
    paragraph._p.insert(0, start)
    paragraph._p.append(end)


def hyperlink(paragraph, title, anchor):
    link = OxmlElement("w:hyperlink")
    link.set(qn("w:anchor"), anchor)
    run = OxmlElement("w:r")
    props = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), TEAL)
    props.append(color)
    run.append(props)
    text = OxmlElement("w:t")
    text.text = title
    run.append(text)
    link.append(run)
    paragraph._p.append(link)


def styles(document):
    section = document.sections[0]
    section.page_width, section.page_height = Inches(8.2677), Inches(11.6929)
    section.top_margin, section.bottom_margin = Inches(0.68), Inches(0.64)
    section.left_margin, section.right_margin = Inches(0.65), Inches(0.65)
    section.header_distance, section.footer_distance = Inches(0.28), Inches(0.27)
    section.different_first_page_header_footer = True
    normal = document.styles["Normal"]
    normal.font.name, normal.font.size, normal.font.color.rgb = "Segoe UI", Pt(9.7), rgb(INK)
    normal.paragraph_format.line_spacing = 1.12
    normal.paragraph_format.space_after = Pt(5.3)
    normal.paragraph_format.widow_control = True
    for name, size, color in (("Heading 1", 20, INK), ("Heading 2", 11.3, TEAL)):
        style = document.styles[name]
        style.font.name, style.font.size, style.font.color.rgb = "Segoe UI", Pt(size), rgb(color)
        style.font.bold = True
        style.paragraph_format.space_before = Pt(8 if name == "Heading 2" else 0)
        style.paragraph_format.space_after = Pt(5)
        style.paragraph_format.keep_with_next = True
    for name, size, color in (("Guide Intro", 10.2, MUTED), ("Guide Caption", 8.2, MUTED),
                             ("Guide Kicker", 8.8, TEAL), ("Guide Table", 8.6, INK),
                             ("Guide Step", 9.7, INK), ("Guide Code", 9.1, INK)):
        style = document.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        style.base_style = normal
        style.font.name, style.font.size, style.font.color.rgb = "Segoe UI", Pt(size), rgb(color)
    document.styles["Guide Intro"].paragraph_format.space_after = Pt(9)
    document.styles["Guide Kicker"].font.bold = True
    document.styles["Guide Kicker"].paragraph_format.space_after = Pt(3)
    document.styles["Guide Kicker"].paragraph_format.keep_with_next = True
    document.styles["Guide Table"].paragraph_format.space_after = Pt(0)
    document.styles["Guide Table"].paragraph_format.line_spacing = 1.06
    document.styles["Guide Step"].paragraph_format.left_indent = Inches(0.19)
    document.styles["Guide Step"].paragraph_format.first_line_indent = Inches(-0.19)
    document.styles["Guide Step"].paragraph_format.space_after = Pt(4.5)
    document.styles["Guide Code"].font.name = "Consolas"
    document.styles["Guide Code"].paragraph_format.space_before = Pt(5)
    document.styles["Guide Code"].paragraph_format.space_after = Pt(7)
    document.styles["Guide Caption"].paragraph_format.space_after = Pt(8)
    document.core_properties.title = "Floodline User Guide"
    document.core_properties.subject = "Using the synthetic CAA prototype, its construction and completion status"
    document.core_properties.author = "Floodline CAA Project"
    document.core_properties.keywords = "Floodline, user guide, synthetic prototype, CAA"
    update = OxmlElement("w:updateFields")
    update.set(qn("w:val"), "true")
    document.settings.element.append(update)
    header = section.header.paragraphs[0]
    header.paragraph_format.space_after = Pt(0)
    header.paragraph_format.tab_stops.add_tab_stop(Inches(6.96), WD_ALIGN_PARAGRAPH.RIGHT)
    run = header.add_run(f"FLOODLINE  /  USER GUIDE\tV{VERSION} · SYNTHETIC DEMO")
    run.font.name, run.font.size, run.font.color.rgb = "Segoe UI", Pt(7.8), rgb(MUTED)
    border = OxmlElement("w:pBdr")
    xml_border(border, "w:bottom")
    header._p.get_or_add_pPr().append(border)
    footer = section.footer.paragraphs[0]
    footer.paragraph_format.tab_stops.add_tab_stop(Inches(6.96), WD_ALIGN_PARAGRAPH.RIGHT)
    rich(footer, "CAA project · Synthetic conditions\t", size=7.6, color=MUTED)
    rich(footer, "Page ", size=7.6, color=MUTED)
    field(footer, "PAGE")
    rich(footer, " of ", size=7.6, color=MUTED)
    field(footer, "NUMPAGES", "22")


def add_figure(document, name, caption, maximum_height):
    path = DISPLAY / f"{name}.png"
    width, height = Image.open(path).size
    rendered_width = min(PAGE_WIDTH, maximum_height * width / height)
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_after = Pt(3)
    paragraph.paragraph_format.keep_with_next = True
    picture = paragraph.add_run().add_picture(str(path), width=Pt(rendered_width))
    picture._inline.docPr.set("descr", caption)
    caption_paragraph = document.add_paragraph(style="Guide Caption")
    caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_paragraph.add_run(caption)


def add_note(document, title, text):
    table = document.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    cell = table.cell(0, 0)
    cell.width = Pt(PAGE_WIDTH)
    shade(cell, PALE)
    cell_margins(cell, top=110, bottom=110, left=150, right=150)
    table.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_after = Pt(3)
    rich(paragraph, title, size=9.5, color=TEAL, bold=True)
    paragraph = cell.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(0)
    rich(paragraph, text, size=9.2)


def add_table(document, block):
    cols = len(block["headers"])
    widths = block.get("widths") or [1 / cols] * cols
    table = document.add_table(rows=1, cols=cols)
    table.alignment, table.autofit = WD_TABLE_ALIGNMENT.CENTER, False
    for column, ratio in zip(table.columns, widths):
        column.width = Pt(PAGE_WIDTH * ratio)
    head = table.rows[0]
    repeated = OxmlElement("w:tblHeader")
    head._tr.get_or_add_trPr().append(repeated)
    for idx, title in enumerate(block["headers"]):
        cell = head.cells[idx]
        cell.width = Pt(PAGE_WIDTH * widths[idx])
        shade(cell, INK)
        cell_margins(cell, top=100, bottom=100)
        paragraph = cell.paragraphs[0]
        paragraph.style = document.styles["Guide Table"]
        rich(paragraph, title, size=8.8, color="FFFFFF", bold=True)
    for row_index, values in enumerate(block["rows"]):
        row = table.add_row()
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        for idx, value in enumerate(values):
            cell = row.cells[idx]
            cell.width = Pt(PAGE_WIDTH * widths[idx])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
            cell_margins(cell)
            shade(cell, "F4F7F8" if row_index % 2 == 0 else "FFFFFF")
            paragraph = cell.paragraphs[0]
            paragraph.style = document.styles["Guide Table"]
            rich(paragraph, str(value), size=8.6, bold=idx == 0)


def build_word():
    document = Document()
    styles(document)
    rich(document.add_paragraph(), "FLOODLINE  /  CAA PROJECT", size=10, color=TEAL, bold=True)
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(25)
    paragraph.paragraph_format.space_after = Pt(0)
    rich(paragraph, TITLE, size=43, color=INK, bold=True)
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(15)
    rich(paragraph, SUBTITLE, size=32, color=INK)
    rich(document.add_paragraph(), "Use the app. Understand its evidence.\nKnow what is finished and what comes next.", size=14, color=MUTED)
    rich(document.add_paragraph(), f"Version {VERSION}  ·  {DATE}", size=10, color=TEAL, bold=True)
    add_figure(document, "03-dark-map", "Floodline's synthetic map and area-evidence view in Dark appearance.", 274)
    add_note(document, "Working local prototype", "Step-by-step instructions for the flood map, reports, routes, alerts and moderator review, followed by the build explanation and completion checklist.")
    rich(document.add_paragraph(), "All pilot locations and environmental conditions are synthetic. Real flood forecasting, external notifications and production hosting still need their own evidence.", size=9.7, color=MUTED)
    first_footer = document.sections[0].first_page_footer.paragraphs[0]
    rich(first_footer, f"Prepared for the Smart City Flood Prediction and Community Alert Platform · {DATE}", size=7.4, color=MUTED)

    contents_heading = document.add_heading("Contents", 1)
    contents_heading.paragraph_format.page_break_before = True
    intro = document.add_paragraph(style="Guide Intro")
    intro.add_run("Click a section title or its page number to jump to it. Begin with setup, then follow the task you want to complete.")
    table = document.add_table(rows=0, cols=2)
    table.autofit = False
    table.columns[0].width, table.columns[1].width = Pt(450), Pt(51)
    for index, page in enumerate(PAGES, 1):
        row = table.add_row()
        left, right = row.cells
        left.width, right.width = Pt(450), Pt(51)
        for cell in row.cells:
            cell_margins(cell, top=77, bottom=77, left=0, right=0)
        paragraph = left.paragraphs[0]
        paragraph.paragraph_format.space_after = Pt(0)
        hyperlink(paragraph, f"{index:02d}  {page['title']}", f"guide_{index:02d}")
        paragraph = right.paragraphs[0]
        paragraph.paragraph_format.space_after = Pt(0)
        paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        field(paragraph, f"PAGEREF guide_{index:02d} \\h", str(index + 2))
    document.add_paragraph()
    add_note(document, "Choose a reading path", "First-time resident: sections 02–09. Moderator: sections 10–13. CAA presenter or assessor: sections 01 and 14–17. Help with a problem: sections 18–20.")

    for index, page in enumerate(PAGES, 1):
        kicker = document.add_paragraph(f"SECTION {index:02d}", style="Guide Kicker")
        kicker.paragraph_format.page_break_before = True
        heading = document.add_heading(page["title"], 1)
        bookmark(heading, f"guide_{index:02d}", index)
        document.add_paragraph(page["intro"], style="Guide Intro")
        for block_index, block in enumerate(page["blocks"]):
            kind = block["kind"]
            if kind == "paragraph":
                rich(document.add_paragraph(), block["text"])
            elif kind == "subheading":
                document.add_heading(block["text"], 2)
            elif kind in ("steps", "bullets"):
                for item_index, item in enumerate(block["items"], 1):
                    paragraph = document.add_paragraph(style="Guide Step")
                    prefix = f"{item_index}. " if kind == "steps" else "• "
                    rich(paragraph, prefix, color=TEAL, bold=True)
                    rich(paragraph, item)
            elif kind == "note":
                add_note(document, block["title"], block["text"])
            elif kind == "table":
                add_table(document, block)
            elif kind == "figure":
                add_figure(document, block["name"], block["caption"], block["height"])
            elif kind == "code":
                paragraph = document.add_paragraph(block["text"], style="Guide Code")
                background = OxmlElement("w:shd")
                background.set(qn("w:fill"), "F0F4F6")
                paragraph._p.get_or_add_pPr().append(background)
            else:
                raise ValueError(f"Unsupported content block: {kind}")
            if kind in ("table", "note") and block_index < len(page["blocks"]) - 1:
                gap = document.add_paragraph()
                gap.paragraph_format.line_spacing = Pt(1)
                gap.paragraph_format.space_before = Pt(0)
                gap.paragraph_format.space_after = Pt(4)
                gap.add_run().font.size = Pt(1)
    document.save(DOCX)


def slug(index, title):
    return f"{index:02d}-" + re.sub(r"[^a-z0-9 ]", "", title.lower()).replace(" ", "-")


def build_markdown():
    lines = ["# Floodline user guide", "", f"Version {VERSION} · {DATE}", "",
             "[Printable PDF](../outputs/Floodline_User_Guide.pdf) · [Editable Word document](../outputs/Floodline_User_Guide.docx)", "",
             "Floodline is a working local synthetic CAA prototype. This guide explains what it does, how to use every screen, how it was built and what is complete or still pending.", "",
             "> All pilot locations, environmental observations and event labels are invented. The relative warning index is not a validated flood probability. Alerts use a simulated in-app adapter.", "",
             "## Contents", ""]
    lines.extend(f"- [{i:02d}. {page['title']}](#{slug(i, page['title'])})" for i, page in enumerate(PAGES, 1))
    lines += ["", "First-time resident: 02–09. Moderator: 10–13. CAA presenter/assessor: 01 and 14–17. Troubleshooting and reference: 18–20.", ""]
    for index, page in enumerate(PAGES, 1):
        lines += [f"## {index:02d}. {page['title']}", "", page["intro"], ""]
        for block in page["blocks"]:
            kind = block["kind"]
            if kind == "paragraph":
                lines += [block["text"], ""]
            elif kind == "subheading":
                lines += [f"### {block['text']}", ""]
            elif kind in ("steps", "bullets"):
                lines.extend((f"{i}. " if kind == "steps" else "- ") + value for i, value in enumerate(block["items"], 1))
                lines.append("")
            elif kind == "note":
                lines += [f"> **{block['title']}.** {block['text']}", ""]
            elif kind == "table":
                esc = lambda value: str(value).replace("|", "\\|").replace("\n", "<br>")
                lines.append("| " + " | ".join(esc(x) for x in block["headers"]) + " |")
                lines.append("| " + " | ".join("---" for _ in block["headers"]) + " |")
                lines.extend("| " + " | ".join(esc(x) for x in row) + " |" for row in block["rows"])
                lines.append("")
            elif kind == "figure":
                lines += [f"![{block['caption']}](user-guide/images/display/{block['name']}.png)", "", f"*{block['caption']}*", ""]
            elif kind == "code":
                lines += ["```powershell", block["text"], "```", ""]
    lines += ["Guide build source: [shared content](../outputs/_build/user_guide/guide_content.py) and [document builder](../outputs/_build/user_guide/build_user_guide.py). Fresh screen walkthrough: [record](../outputs/_qa/user-guide/walkthrough.json).", ""]
    MARKDOWN.write_text("\n".join(lines), encoding="utf-8")


def export_pdf():
    import pythoncom
    from win32com.client import DispatchEx
    pythoncom.CoInitialize()
    word = None
    document = None
    try:
        word = DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        document = word.Documents.Open(str(DOCX), ReadOnly=False, AddToRecentFiles=False)
        document.Repaginate()
        document.Fields.Update()
        for section in document.Sections:
            for footer in section.Footers:
                footer.Range.Fields.Update()
        document.Repaginate()
        document.Fields.Update()
        sections = [{"section": i, "title": page["title"],
                     "page": document.Bookmarks(f"guide_{i:02d}").Range.Information(3)}
                    for i, page in enumerate(PAGES, 1)]
        document.Save()
        document.ExportAsFixedFormat(OutputFileName=str(PDF), ExportFormat=17,
                                    OpenAfterExport=False, OptimizeFor=0,
                                    Item=0, IncludeDocProps=True, KeepIRM=True,
                                    CreateBookmarks=1, DocStructureTags=True,
                                    BitmapMissingFonts=True, UseISO19005_1=False)
        (QA / "word-layout.json").write_text(json.dumps({"sections": sections,
             "pages": document.ComputeStatistics(2), "engine": "Microsoft Word"}, indent=2), encoding="utf-8")
    finally:
        if document is not None:
            document.Close(SaveChanges=False)
        if word is not None:
            word.Quit()
        pythoncom.CoUninitialize()


def verify_and_render():
    import fitz
    with fitz.open(PDF) as pdf:
        text = "\n".join(page.get_text() for page in pdf)
        missing = [page["title"] for page in PAGES if page["title"] not in text]
        assert not missing, missing
        assert pdf.page_count >= 22
        thumbnails = []
        page_counts = []
        links = 0
        for index, page in enumerate(pdf):
            page_counts.append(len(page.get_text().strip()))
            links += len(page.get_links())
            pixmap = page.get_pixmap(matrix=fitz.Matrix(0.55, 0.55), alpha=False)
            thumbnail = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
            label_image = Image.new("RGB", (thumbnail.width, thumbnail.height + 28), "#EAF0F2")
            label_image.paste(thumbnail, (0, 0))
            ImageDraw.Draw(label_image).text((8, thumbnail.height + 4), f"Page {index + 1}", font=font(14), fill="#203741")
            thumbnails.append(label_image)
        cols = 4
        tw, th = thumbnails[0].size
        contact = Image.new("RGB", (cols * (tw + 12) + 12, ((len(thumbnails) + cols - 1) // cols) * (th + 12) + 12), "#DCE7EA")
        for index, thumbnail in enumerate(thumbnails):
            contact.paste(thumbnail, (12 + (index % cols) * (tw + 12), 12 + (index // cols) * (th + 12)))
        contact.save(QA / "contact-sheet.jpg", quality=92)
        assert min(page_counts) > 100, "A blank or nearly blank page was produced."
        (QA / "pdf-extracted-text.txt").write_text(text, encoding="utf-8")
        record = {"status": "passed", "built_at": datetime.now(timezone.utc).isoformat(),
                  "pages": pdf.page_count, "sections": len(PAGES), "links": links,
                  "missing_sections": missing, "characters_per_page": page_counts,
                  "pdf_engine": "Microsoft Word", "files": []}
        for path in (PDF, DOCX, MARKDOWN):
            record["files"].append({"file": str(path.relative_to(ROOT)), "bytes": path.stat().st_size,
                                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        (QA / "document-verification.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
        print(json.dumps({"pages": pdf.page_count, "sections": len(PAGES), "pdf_links": links,
                          "files": record["files"]}, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-pdf", action="store_true")
    args = parser.parse_args()
    OUTPUT.mkdir(exist_ok=True)
    QA.mkdir(parents=True, exist_ok=True)
    prepare_assets()
    build_word()
    build_markdown()
    print("Markdown and Word guide built.", flush=True)
    if not args.skip_pdf:
        export_pdf()
        verify_and_render()


if __name__ == "__main__":
    main()
