from __future__ import annotations

import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

import fitz
from PIL import Image, ImageDraw
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, KeepTogether, NextPageTemplate,
    PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Smart_City_Flood_Prediction_CAA_Pipeline.md"
OUTPUT = ROOT / "Smart_City_Flood_Prediction_CAA_Pipeline.pdf"
QA = ROOT / "_qa"
QA.mkdir(parents=True, exist_ok=True)

FONT_ROOT = Path("C:/Windows/Fonts")
for name, filename in (
    ("Calibri", "calibri.ttf"), ("Calibri-Bold", "calibrib.ttf"),
    ("Calibri-Italic", "calibrii.ttf"), ("Calibri-BoldItalic", "calibriz.ttf"),
):
    pdfmetrics.registerFont(TTFont(name, str(FONT_ROOT / filename)))
pdfmetrics.registerFontFamily(
    "Calibri", normal="Calibri", bold="Calibri-Bold",
    italic="Calibri-Italic", boldItalic="Calibri-BoldItalic",
)

NAVY = colors.HexColor("#153246")
TEAL = colors.HexColor("#087F82")
INK = colors.HexColor("#233746")
MUTED = colors.HexColor("#536878")
PALE = colors.HexColor("#EEF6F6")
RULE = colors.HexColor("#D9E4E8")
AMBER = colors.HexColor("#B87520")
WHITE = colors.white
PAGE_W, PAGE_H = A4
MARGIN = 43
WIDTH = PAGE_W - 2 * MARGIN
TOTAL_PAGES = 18

STYLE = {
    "body": ParagraphStyle("Body", fontName="Calibri", fontSize=10.5, leading=14.0,
                           textColor=INK, spaceAfter=6.4),
    "small": ParagraphStyle("Small", fontName="Calibri", fontSize=9.25, leading=12.0,
                            textColor=MUTED, spaceAfter=5),
    "title": ParagraphStyle("Title", fontName="Calibri-Bold", fontSize=23, leading=27,
                            textColor=NAVY, spaceAfter=12),
    "h2": ParagraphStyle("H2", fontName="Calibri-Bold", fontSize=12, leading=15,
                         textColor=TEAL, spaceBefore=8, spaceAfter=5, keepWithNext=True),
    "bullet": ParagraphStyle("Bullet", fontName="Calibri", fontSize=10.5, leading=14,
                             leftIndent=11, firstLineIndent=-10, textColor=INK, spaceAfter=4.5),
    "cell": ParagraphStyle("Cell", fontName="Calibri", fontSize=9.3, leading=12.1,
                           textColor=INK),
    "head": ParagraphStyle("TableHead", fontName="Calibri-Bold", fontSize=9.3, leading=12,
                           textColor=WHITE),
    "callout": ParagraphStyle("Callout", fontName="Calibri", fontSize=10.2, leading=13.6,
                              textColor=NAVY),
}


def inline(text: str) -> str:
    text = escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", r"<font name='Calibri-Bold'>\1</font>", text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)",
                  r"<link href='\2' color='#087F82'><u>\1</u></link>", text)
    return text


def p(text: str, style: str = "body") -> Paragraph:
    return Paragraph(inline(text), STYLE[style])


def draw_text(canvas, text, x, y_top, width, size=10.5, leading=14,
              color=INK, bold=False):
    style = ParagraphStyle("Drawing", fontName="Calibri-Bold" if bold else "Calibri",
                           fontSize=size, leading=leading, textColor=color,
                           alignment=TA_LEFT)
    paragraph = Paragraph(inline(text), style)
    _, height = paragraph.wrap(width, PAGE_H)
    paragraph.drawOn(canvas, x, y_top - height)
    return height


class Pipeline(Flowable):
    def __init__(self):
        super().__init__()
        self.width = WIDTH
        self.height = 349

    def draw(self):
        c = self.canv
        stages = [
            ("01", "Collect evidence", "Rainfall, water levels, terrain, roads and reports", "M1 + M2"),
            ("02", "Check and align", "Units, timestamps, missingness, location and provenance", "M1 + M4"),
            ("03", "Build GIS features", "Join data to cells; compute rainfall and terrain features", "M2 + M3"),
            ("04", "Estimate flood risk", "Baseline / model + valid time + data-support status", "M3"),
            ("05", "Apply decision rules", "Freshness, verification, thresholds and alert cooldown", "M4 + M6"),
            ("06", "Publish useful actions", "Risk map, opt-in alerts and routes avoiding known hazards", "M2 + M5 + M6"),
            ("07", "Review and learn", "Moderated reports, delivery logs and historical evaluation", "ALL SIX"),
        ]
        row_h = 41
        gap = 8
        for idx, (number, title, detail, owner) in enumerate(stages):
            y = self.height - (idx + 1) * row_h - idx * gap
            c.setFillColor(PALE if idx % 2 == 0 else colors.HexColor("#F6F8FA"))
            c.roundRect(0, y, WIDTH, row_h, 5, fill=1, stroke=0)
            c.setFillColor(TEAL)
            c.circle(21, y + row_h / 2, 11, fill=1, stroke=0)
            c.setFont("Calibri-Bold", 9)
            c.setFillColor(WHITE)
            c.drawCentredString(21, y + row_h / 2 - 3, number)
            draw_text(c, title, 42, y + 34, 320, 11, 13, NAVY, True)
            draw_text(c, detail, 42, y + 19, 350, 9.0, 10.3, MUTED)
            c.setFillColor(TEAL)
            c.setFont("Calibri-Bold", 8.0)
            c.drawRightString(WIDTH - 10, y + 27, owner)
            if idx < len(stages) - 1:
                c.setStrokeColor(TEAL)
                c.setLineWidth(0.9)
                c.line(21, y - 1, 21, y - gap + 1)
                c.line(18.5, y - gap + 4, 21, y - gap + 1)
                c.line(23.5, y - gap + 4, 21, y - gap + 1)


class Architecture(Flowable):
    def __init__(self):
        super().__init__()
        self.width = WIDTH
        self.height = 165

    def draw(self):
        c = self.canv
        gap = 10
        cw = (WIDTH - 2 * gap) / 3
        cards = [
            (0, 113, "External data / simulator", "M1 adapters; retain raw evidence"),
            (cw + gap, 113, "Resident + admin web app", "M5; Leaflet map and report form"),
            (2 * (cw + gap), 113, "Notification adapter", "M6; opt-in test delivery + logs"),
            (0, 56, "Scheduled worker", "M1 / M3; ingest, features, inference"),
            (cw + gap, 56, "FastAPI application", "M4; auth, reports, routes, risk API"),
            (2 * (cw + gap), 56, "Alert decision worker", "M6; deduplication, expiry, retries"),
            (0, 0, "PostgreSQL + PostGIS", "Versioned geodata and event records"),
            (cw + gap, 0, "Private image storage", "Cleaned uploads; short-lived access"),
            (2 * (cw + gap), 0, "Model + run registry", "Artifact, features, split and version"),
        ]
        for x, y, title, detail in cards:
            c.setFillColor(PALE if y != 56 else NAVY)
            c.roundRect(x, y, cw, 43, 4, fill=1, stroke=0)
            draw_text(c, title, x + 8, y + 34, cw - 16, 9.2, 10.8,
                      WHITE if y == 56 else NAVY, True)
            draw_text(c, detail, x + 8, y + 20, cw - 16, 8.3, 10,
                      colors.HexColor("#DCECEE") if y == 56 else MUTED)
        c.setStrokeColor(TEAL)
        c.setLineWidth(0.8)
        centres = (cw / 2, cw + gap + cw / 2, 2 * (cw + gap) + cw / 2)
        for index, x in enumerate(centres):
            c.line(x, 113, x, 101)
            if index < 2:
                c.line(x - 2.5, 104, x, 101)
                c.line(x + 2.5, 104, x, 101)
            if index > 0:
                c.line(x - 2.5, 110, x, 113)
                c.line(x + 2.5, 110, x, 113)
            c.line(x, 56, x, 44)
            c.line(x - 2.5, 47, x, 44)
            c.line(x + 2.5, 47, x, 44)
        # Shared persistence boundary: all services can reach the appropriate store.
        c.line(centres[0], 50, centres[-1], 50)
        c.line(cw, 77, cw + gap, 77)
        c.line(2 * cw + gap, 77, 2 * (cw + gap), 77)


def table(rows, fractions=None):
    if fractions is None:
        fractions = [1 / len(rows[0])] * len(rows[0])
    total = sum(fractions)
    widths = [WIDTH * fraction / total for fraction in fractions]
    data = [[p(cell, "head" if row_index == 0 else "cell") for cell in row]
            for row_index, row in enumerate(rows)]
    result = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F1F6F7"), WHITE]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, NAVY),
        ("LINEBELOW", (0, 1), (-1, -1), 0.35, RULE),
    ]))
    return result


def callout(text):
    result = Table([[p(text, "callout")]], colWidths=[WIDTH])
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE),
        ("LINEBEFORE", (0, 0), (0, -1), 2.5, TEAL),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    return KeepTogether([Spacer(1, 3), result, Spacer(1, 7)])


def parse_page(chunk):
    lines = chunk.strip().splitlines()
    title = lines[0].removeprefix("# ").strip()
    items = [p(title, "title")]
    widths = None
    i = 1
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("<!-- widths:"):
            widths = [float(x.strip()) for x in line[12:].replace("-->", "").split(",")]
        elif line == "[PIPELINE]":
            items.extend([Pipeline(), Spacer(1, 7)])
        elif line == "[ARCHITECTURE]":
            items.extend([Architecture(), Spacer(1, 6)])
        elif line.startswith("## "):
            items.append(p(line[3:], "h2"))
        elif line.startswith("> "):
            items.append(callout(line[2:]))
        elif line.startswith("| "):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [cell.strip() for cell in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"[-: ]+", cell) for cell in cells):
                    rows.append(cells)
                i += 1
            items.extend([table(rows, widths), Spacer(1, 8)])
            widths = None
            continue
        elif line.startswith("- "):
            items.append(p("• " + line[2:], "bullet"))
        elif line.startswith("~ "):
            items.append(p(line[2:], "small"))
        else:
            paragraph = [line]
            while i + 1 < len(lines) and lines[i + 1].strip() and not lines[i + 1].startswith(("#", "|", "- ", "> ", "<!--", "[PIPELINE]", "[ARCHITECTURE]", "~ ")):
                i += 1
                paragraph.append(lines[i].strip())
            items.append(p(" ".join(paragraph)))
        i += 1
    return title, items


def cover(canvas, doc):
    c = canvas
    c.saveState()
    c.setFillColor(NAVY)
    c.rect(0, 422, PAGE_W, PAGE_H - 422, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#28495A"))
    c.setLineWidth(0.8)
    for offset in range(8):
        c.arc(PAGE_W - 180 - offset * 20, 590 - offset * 17,
              PAGE_W + 80 + offset * 20, 850 + offset * 17,
              startAng=90, extent=180)
    draw_text(c, "CAA  /  PROJECT IMPLEMENTATION BLUEPRINT", MARGIN, 791, 420,
              10, 12, colors.HexColor("#9ADBD7"), True)
    for label, y in (("Smart City", 731), ("Flood Prediction", 690),
                     ("and Community", 649), ("Alert Platform", 608)):
        draw_text(c, label, MARGIN, y, WIDTH, 34, 40, WHITE, True)
    draw_text(c, "A detailed, practical pipeline for a six-person team", MARGIN, 549,
              WIDTH, 13, 17, colors.HexColor("#D9E8ED"))
    c.setStrokeColor(colors.HexColor("#447380"))
    c.line(MARGIN, 510, PAGE_W - MARGIN, 510)
    draw_text(c, "Rainfall + water levels  →  GIS + prediction  →  community action",
              MARGIN, 490, WIDTH, 11.0, 15, colors.HexColor("#B8DDD9"))
    card_w = (WIDTH - 20) / 3
    for index, (big, label) in enumerate((("6 members", "Clear ownership and handoffs"),
                                        ("8 weeks", "Proposed delivery schedule"),
                                        ("1 pilot area", "A focused, testable prototype"))):
        x = MARGIN + index * (card_w + 10)
        c.setFillColor(PALE)
        c.roundRect(x, 327, card_w, 65, 5, fill=1, stroke=0)
        draw_text(c, big, x + 11, 377, card_w - 22, 18, 22, TEAL, True)
        draw_text(c, label, x + 11, 348, card_w - 22, 9.1, 11, MUTED)
    draw_text(c, "PURPOSE", MARGIN, 299, WIDTH, 9, 12, TEAL, True)
    draw_text(c, "Turn limited environmental and geographic data into a prototype that identifies flood-prone areas, visualises risk, receives community evidence and communicates useful alerts with uncertainty.",
              MARGIN, 277, WIDTH, 12, 17, INK)
    draw_text(c, "READING GUIDE", MARGIN, 205, WIDTH, 9, 12, TEAL, True)
    guide = [
        ("02–05", "Project scope, complete pipeline and six-person ownership"),
        ("06–10", "Data, GIS, prediction, validation and system architecture"),
        ("11–13", "Community reports, alerts, map design and route suggestions"),
        ("14–18", "Schedule, testing, deployment, submission and references"),
    ]
    for idx, (pages, label) in enumerate(guide):
        y = 183 - idx * 22
        draw_text(c, pages, MARGIN, y, 51, 10.3, 13, TEAL, True)
        draw_text(c, label, MARGIN + 58, y, WIDTH - 58, 10.3, 13, INK)
    draw_text(c, "Based on project description.docx, item 3. Team names, city and course deadlines can be filled in later. Timelines and numerical targets are planning assumptions, not measured results.",
              MARGIN, 79, WIDTH, 8.6, 11.1, MUTED)
    c.setFont("Calibri", 7.8)
    c.setFillColor(MUTED)
    c.drawString(MARGIN, 26, "Prepared 08 November 2026  •  CAA project pipeline")
    c.drawRightString(PAGE_W - MARGIN, 26, "01 / 18")
    c.restoreState()


def body(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(TEAL)
    canvas.setFont("Calibri-Bold", 8.0)
    canvas.drawString(MARGIN, PAGE_H - 30, "CAA  /  SMART CITY FLOOD PLATFORM")
    canvas.setFillColor(MUTED)
    canvas.setFont("Calibri", 8.0)
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 30, "SIX-PERSON IMPLEMENTATION PIPELINE")
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.6)
    canvas.line(MARGIN, PAGE_H - 40, PAGE_W - MARGIN, PAGE_H - 40)
    canvas.line(MARGIN, 42, PAGE_W - MARGIN, 42)
    canvas.setFont("Calibri", 7.7)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN, 26, "Smart City Flood Prediction and Community Alert Platform")
    canvas.drawRightString(PAGE_W - MARGIN, 26, f"{doc.page:02d} / {TOTAL_PAGES}")
    canvas.restoreState()


class Document(BaseDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "Title":
            label = flowable.getPlainText()
            key = f"section-{self.page}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(label, key, level=0, closed=False)


def main():
    chunks = SOURCE.read_text(encoding="utf-8").split("<!-- PAGE -->")
    sections = [parse_page(chunk) for chunk in chunks[1:]]
    if len(sections) != TOTAL_PAGES - 1:
        raise ValueError(f"Expected 17 body sections; got {len(sections)}")
    document = Document(str(OUTPUT), pagesize=A4, rightMargin=MARGIN,
                        leftMargin=MARGIN, topMargin=57, bottomMargin=52,
                        title="Smart City Flood Prediction and Community Alert Platform | Six-Person CAA Pipeline",
                        author="CAA Project Team", subject="Detailed implementation pipeline, ownership and validation plan",
                        pageCompression=1)
    frame = Frame(MARGIN, 52, WIDTH, PAGE_H - 109,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    document.addPageTemplates([
        PageTemplate(id="Cover", frames=[frame], onPage=cover),
        PageTemplate(id="Body", frames=[frame], onPage=body),
    ])
    story = [Spacer(1, 1), NextPageTemplate("Body"), PageBreak()]
    for idx, (title, items) in enumerate(sections):
        story.extend(items)
        if idx < len(sections) - 1:
            story.append(PageBreak())
    document.build(story)
    pdf = fitz.open(OUTPUT)
    expected_titles = ["Smart City"] + [title for title, _ in sections]
    checks = []
    for idx, page in enumerate(pdf):
        text = page.get_text()
        expected = expected_titles[idx] if idx < len(expected_titles) else "UNEXPECTED OVERFLOW PAGE"
        norm = lambda value: re.sub(r"\s+", " ", value).strip()
        checks.append({"page": idx + 1, "expected_title": expected,
                       "title_present": norm(expected) in norm(text),
                       "word_count": len(text.split()),
                       "link_count": len(page.get_links())})
    result = {"pdf": str(OUTPUT), "pages": len(pdf),
              "size_bytes": OUTPUT.stat().st_size,
              "total_words": sum(row["word_count"] for row in checks),
              "checks": checks}
    (QA / "verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    thumb_w = 238
    thumb_h = round(thumb_w * PAGE_H / PAGE_W)
    columns = 3
    rows = (len(pdf) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * (thumb_w + 14) + 14,
                              rows * (thumb_h + 31) + 12), "#dfe6ea")
    draw = ImageDraw.Draw(sheet)
    for idx, page in enumerate(pdf):
        pix = page.get_pixmap(matrix=fitz.Matrix(thumb_w / PAGE_W, thumb_w / PAGE_W), alpha=False)
        thumb = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        x = 14 + idx % columns * (thumb_w + 14)
        y = 12 + idx // columns * (thumb_h + 31)
        sheet.paste(thumb, (x, y))
        draw.text((x, y + thumb_h + 3), f"Page {idx + 1:02d}", fill="#153246")
    sheet.save(QA / "contact_sheet.png")
    for number in (1, 3, 4, 10, 14, 18):
        if number <= len(pdf):
            pdf[number - 1].get_pixmap(matrix=fitz.Matrix(1.65, 1.65), alpha=False).save(QA / f"page_{number:02d}.png")
    print(json.dumps(result, indent=2))
    if len(pdf) != TOTAL_PAGES or not all(row["title_present"] for row in checks):
        raise SystemExit("PDF pagination check failed; review overflow before delivery.")


if __name__ == "__main__":
    main()
