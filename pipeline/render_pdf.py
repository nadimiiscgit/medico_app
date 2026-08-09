"""Phase 5 — render chapters into printable PDFs.

reportlab, because it is a pure-Python wheel with a real table of contents that
resolves page numbers (weasyprint needs system libraries; pandoc and LaTeX are
not installed here).

Two details that matter more than they look:

  Fonts.  reportlab's built-in Helvetica has no Greek letters, arrows or
          sub/superscripts and silently renders them as solid black boxes.
          DejaVu is registered instead and vendored into pipeline/fonts so the
          build behaves identically on another machine.

  Questions.  Printed from the corpus at render time, never from chapter text.
          The chapter stores only question ids, so the stem, options, answer
          and explanation in the PDF are always the verbatim originals.

Usage:
    python3 -m pipeline.render_pdf --subject Pharmacology
    python3 -m pipeline.render_pdf --all
    python3 -m pipeline.render_pdf --index --high-yield
"""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether,
                                NextPageTemplate, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

from . import dataio, paths

BODY = "DejaVu"
ACCENT = colors.HexColor("#1f4e79")
MUTED = colors.HexColor("#5a6472")
RULE = colors.HexColor("#c9d2dd")
BOXBG = colors.HexColor("#f4f7fa")
TIER_COLOUR = {"A": colors.HexColor("#b3261e"),
               "B": colors.HexColor("#7a5200"),
               "C": colors.HexColor("#3c4858")}


def register_fonts() -> None:
    faces = {
        BODY: "DejaVuSans.ttf",
        f"{BODY}-Bold": "DejaVuSans-Bold.ttf",
        f"{BODY}-Oblique": "DejaVuSans-Oblique.ttf",
        f"{BODY}-BoldOblique": "DejaVuSans-BoldOblique.ttf",
    }
    for name, filename in faces.items():
        path = paths.FONTS / filename
        if not path.exists():                      # fall back to the system copy
            path = Path("/usr/share/fonts/truetype/dejavu") / filename
        pdfmetrics.registerFont(TTFont(name, str(path)))
    pdfmetrics.registerFontFamily(
        BODY, normal=BODY, bold=f"{BODY}-Bold",
        italic=f"{BODY}-Oblique", boldItalic=f"{BODY}-BoldOblique",
    )


def styles() -> dict:
    base = getSampleStyleSheet()
    s = {
        "title": ParagraphStyle("title", parent=base["Title"], fontName=f"{BODY}-Bold",
                                fontSize=26, leading=31, textColor=ACCENT, spaceAfter=6),
        "subtitle": ParagraphStyle("subtitle", parent=base["Normal"], fontName=BODY,
                                   fontSize=12, leading=16, textColor=MUTED,
                                   alignment=TA_CENTER),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName=f"{BODY}-Bold",
                             fontSize=17, leading=21, textColor=ACCENT,
                             spaceBefore=16, spaceAfter=7),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName=f"{BODY}-Bold",
                             fontSize=12.5, leading=16, textColor=colors.HexColor("#22303f"),
                             spaceBefore=11, spaceAfter=4),
        "body": ParagraphStyle("body", parent=base["Normal"], fontName=BODY,
                               fontSize=9.6, leading=14.2, spaceAfter=5),
        "small": ParagraphStyle("small", parent=base["Normal"], fontName=BODY,
                                fontSize=8.3, leading=11.4, textColor=MUTED),
        # bulletFontName defaults to Helvetica, which has none of these glyphs
        # and renders them as (cid:NNN) or a stray letter.
        "bullet": ParagraphStyle("bullet", parent=base["Normal"], fontName=BODY,
                                 fontSize=9.6, leading=14, leftIndent=11,
                                 bulletIndent=2, spaceAfter=2.5,
                                 bulletFontName=BODY, bulletFontSize=9.6),
        "cell": ParagraphStyle("cell", parent=base["Normal"], fontName=BODY,
                               fontSize=8.4, leading=11.2),
        "cellhead": ParagraphStyle("cellhead", parent=base["Normal"],
                                   fontName=f"{BODY}-Bold", fontSize=8.4,
                                   leading=11.2, textColor=colors.white),
        "qstem": ParagraphStyle("qstem", parent=base["Normal"], fontName=f"{BODY}-Bold",
                                fontSize=9.1, leading=12.6),
        "qopt": ParagraphStyle("qopt", parent=base["Normal"], fontName=BODY,
                               fontSize=8.8, leading=12, leftIndent=8),
        "qans": ParagraphStyle("qans", parent=base["Normal"], fontName=f"{BODY}-Bold",
                               fontSize=8.8, leading=12,
                               textColor=colors.HexColor("#1a6b3c")),
        "qexpl": ParagraphStyle("qexpl", parent=base["Normal"], fontName=BODY,
                                fontSize=8.3, leading=11.5, textColor=colors.HexColor("#2f3a47")),
    }
    s["toc1"] = ParagraphStyle("toc1", fontName=f"{BODY}-Bold", fontSize=10.5,
                               leading=15, spaceBefore=7, textColor=ACCENT)
    s["toc2"] = ParagraphStyle("toc2", fontName=BODY, fontSize=9.2, leading=13,
                               leftIndent=13)
    return s


_BOLD = re.compile(r"\*\*(.+?)\*\*", re.S)
_ITAL = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", re.S)


def rich(text: str) -> str:
    """Escape for reportlab, then re-apply the **bold** / *italic* subset."""
    out = html.escape(str(text or ""), quote=False)
    out = _BOLD.sub(r"<b>\1</b>", out)
    out = _ITAL.sub(r"<i>\1</i>", out)
    return out


class NumberedCanvas(pdfcanvas.Canvas):
    """Two-pass canvas so the footer can print 'Page N of M'."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved)
        for state in self._saved:
            self.__dict__.update(state)
            self.setFont(BODY, 7.6)
            self.setFillColor(MUTED)
            self.drawRightString(A4[0] - 18 * mm, 11 * mm,
                                 f"Page {self._pageNumber} of {total}")
            header = getattr(self, "_running_header", "")
            if header and self._pageNumber > 1:
                self.drawString(18 * mm, A4[1] - 11 * mm, header[:110])
                self.setStrokeColor(RULE)
                self.line(18 * mm, A4[1] - 13 * mm, A4[0] - 18 * mm, A4[1] - 13 * mm)
            super().showPage()
        super().save()


class ChapterDoc(BaseDocTemplate):
    """Feeds headings to the table of contents and records chapter start pages."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chapter_pages: dict[str, int] = {}
        self._header = ""
        self._outline_depth = -1
        self._outline_seq = 0

    def _outline(self, title: str, key: str, level: int) -> None:
        """Add a bookmark, keeping outline levels contiguous.

        reportlab refuses to jump from level -1 straight to level 1, which
        happens whenever a chapter is emitted before its section heading.
        """
        level = min(level, self._outline_depth + 1)
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(title[:80], key, level=level)
        self._outline_depth = level

    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph):
            return
        style = flowable.style.name
        text = re.sub(r"<[^>]+>", "", flowable.getPlainText())
        if style == "h1":
            self.notify("TOCEntry", (0, text, self.page))
            self._outline_seq += 1
            self._outline(text, f"sec-{self._outline_seq}", 0)
        elif style == "h2":
            key = getattr(flowable, "_topicId", None)
            if key:
                self.notify("TOCEntry", (1, text, self.page))
                self.chapter_pages[key] = self.page
                self._outline(text, key, 1)
        if getattr(flowable, "_header", None):
            self.canv._running_header = flowable._header


def _frame_template(name: str) -> PageTemplate:
    frame = Frame(18 * mm, 16 * mm, A4[0] - 36 * mm, A4[1] - 32 * mm, id="body")
    return PageTemplate(id=name, frames=[frame])


def question_box(rec: dict, expl: str, st: dict) -> KeepTogether:
    bits = [Paragraph(rich(rec["question"]), st["qstem"])]

    for img in _images(rec):
        bits.append(Spacer(1, 3))
        bits.append(img)

    for key in ("A", "B", "C", "D"):
        if key in rec.get("options", {}):
            mark = "&#9679;" if key == rec.get("correctAnswer") else "&#9675;"
            bits.append(Paragraph(f"{mark} <b>{key}.</b> {rich(rec['options'][key])}",
                                  st["qopt"]))
    bits.append(Paragraph(f"Answer: {rec.get('correctAnswer','?')}", st["qans"]))
    if expl:
        bits.append(Paragraph(rich(expl[:1600]), st["qexpl"]))

    badge = f"{rec.get('exam','')} {rec.get('year','')}"
    if rec.get("sourceConfidence") == "memory_based":
        badge += "  (memory-based recall)"
    bits.append(Paragraph(badge, st["small"]))

    table = Table([[bits]], colWidths=[A4[0] - 36 * mm])
    table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, RULE),
        ("BACKGROUND", (0, 0), (-1, -1), BOXBG),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return KeepTogether([table, Spacer(1, 5)])


def _images(rec: dict) -> list[Image]:
    """Embed question images, skipping any that are missing rather than failing."""
    urls = ([rec["imageUrl"]] if rec.get("imageUrl") else []) + list(rec.get("imageUrls") or [])
    out = []
    max_w = A4[0] - 52 * mm
    for url in urls[:4]:
        path = paths.PUBLIC / url.lstrip("/")
        if not path.exists():
            continue
        try:
            from PIL import Image as PILImage
            with PILImage.open(path) as im:
                w, h = im.size
            scale = min(max_w / w, (70 * mm) / h, 1.0)
            out.append(Image(str(path), width=w * scale, height=h * scale))
        except Exception:
            continue
    return out


def data_table(section: dict, st: dict) -> KeepTogether:
    cols = section.get("columns") or []
    rows = section.get("rows") or []
    head = [Paragraph(rich(c), st["cellhead"]) for c in cols]
    body = [[Paragraph(rich(c), st["cell"]) for c in row] for row in rows]
    width = A4[0] - 36 * mm
    # Equal columns force long topic names to break mid-word ("Tem poromandibul
    # ar Joint"), so callers can pass relative weights.
    weights = section.get("widths") or [1] * len(cols)
    total = sum(weights) or 1
    col_widths = [width * w / total for w in weights]
    table = Table([head] + body, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("GRID", (0, 0), (-1, -1), 0.4, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BOXBG]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
    ]))
    return KeepTogether([table, Spacer(1, 7)])


def chapter_flowables(ch: dict, by_id: dict, expl: dict, st: dict) -> list:
    flow: list = []
    heading = Paragraph(rich(ch["topic"]), st["h2"])
    heading._topicId = ch["topicId"]
    heading._header = f"{ch['subject']}  >  {ch['section']}  >  {ch['topic']}"
    flow.append(heading)

    meta = (f"Tier {ch['tier']} &nbsp;|&nbsp; ~{ch['highYield']} expected questions "
            f"&nbsp;|&nbsp; {ch['pyqCount']} previous-year questions")
    flow.append(Paragraph(meta, st["small"]))
    flow.append(Spacer(1, 4))
    if ch.get("oneLiner"):
        flow.append(Paragraph(rich(ch["oneLiner"]), st["body"]))

    if ch.get("mustKnow"):
        flow.append(Paragraph("Must know", st["h2"]))
        for item in ch["mustKnow"]:
            flow.append(Paragraph(rich(item), st["bullet"], bulletText="•"))
        flow.append(Spacer(1, 5))

    for sec in ch.get("sections", []):
        kind = sec.get("type")
        if sec.get("heading") and kind != "pyqBank":
            flow.append(Paragraph(rich(sec["heading"]), st["h2"]))

        if kind == "concept":
            for para in str(sec.get("body", "")).split("\n\n"):
                if para.strip():
                    flow.append(Paragraph(rich(para.strip()), st["body"]))
        elif kind == "table":
            flow.append(data_table(sec, st))
        elif kind == "mnemonic":
            flow.append(Paragraph(rich(sec.get("body", "")), st["body"]))
            if sec.get("expansion"):
                flow.append(Paragraph(rich(sec["expansion"]), st["small"]))
        elif kind in ("pitfalls",):
            for item in sec.get("items") or []:
                flow.append(Paragraph(rich(item), st["bullet"], bulletText="!"))
        elif kind == "repeats":
            for item in sec.get("items") or []:
                years = ", ".join(str(y) for y in item.get("years") or [])
                flow.append(Paragraph(
                    f"{rich(item.get('concept',''))} <font color='#5a6472'>({years})</font>",
                    st["bullet"], bulletText="»"))
        elif kind == "crossref":
            for item in sec.get("items") or []:
                if isinstance(item, dict):
                    line = f"<b>{rich(item.get('book',''))}</b>"
                    if item.get("chapter"):
                        line += f" &mdash; {rich(item['chapter'])}"
                    if item.get("note"):
                        line += f". {rich(item['note'])}"
                else:
                    line = rich(item)
                flow.append(Paragraph(line, st["bullet"], bulletText="▸"))
        elif kind == "pyqBank":
            ids = sec.get("questionIds") or []
            flow.append(Paragraph(
                sec.get("heading") or f"Previous-year questions ({len(ids)})", st["h2"]))
            for qid in ids:
                rec = by_id.get(qid)
                if rec:
                    flow.append(question_box(rec, expl.get(qid, {}).get("text", ""), st))
        flow.append(Spacer(1, 2))

    flow.append(Spacer(1, 9))
    return flow


def _cover(title: str, lines: list[str], st: dict) -> list:
    flow = [Spacer(1, 52 * mm), Paragraph(rich(title), st["title"]), Spacer(1, 5)]
    for line in lines:
        flow.append(Paragraph(rich(line), st["subtitle"]))
    flow.append(PageBreak())
    return flow


def _toc(st: dict) -> list:
    toc = TableOfContents()
    toc.levelStyles = [st["toc1"], st["toc2"]]
    return [Paragraph("Contents", st["h1"]), toc, PageBreak()]


def load_chapters(subject: str | None = None) -> list[dict]:
    out = []
    if not paths.CHAPTERS.exists():
        return out
    for path in sorted(paths.CHAPTERS.rglob("*.json")):
        with open(path) as f:
            ch = json.load(f)
        if subject is None or ch.get("subject") == subject:
            out.append(ch)
    return out


def build_subject_pdf(subject: str, index: dict, by_id: dict,
                      expl: dict) -> tuple[Path, dict[str, int]] | None:
    chapters = load_chapters(subject)
    if not chapters:
        return None
    st = styles()
    payload = index["subjects"].get(subject, {})

    order = {}
    for sec in payload.get("sections", []):
        for i, t in enumerate(sec["topics"]):
            order[t["topicId"]] = (sec["section"], -t["highYield"], i)
    chapters.sort(key=lambda c: order.get(c["topicId"], (c["section"], 0, 0)))

    out = paths.OUTPUT_PDF / f"NEETPG_{re.sub(r'[^A-Za-z0-9]+', '_', subject)}.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    doc = ChapterDoc(str(out), pagesize=A4, title=f"NEET PG — {subject}",
                     author="NEET PG topic-wise study material")
    doc.addPageTemplates([_frame_template("body")])

    flow = _cover(
        subject,
        [f"{payload.get('questionCount', 0)} previous-year questions",
         f"~{payload.get('highYield', 0):.0f} expected questions in a 200-question paper",
         f"{len(chapters)} topics, ordered high-yield first",
         "NEET PG 30 August 2026"],
        st,
    )
    flow += _toc(st)

    current = None
    for ch in chapters:
        if ch["section"] != current:
            current = ch["section"]
            flow.append(Paragraph(rich(current), st["h1"]))
        flow += chapter_flowables(ch, by_id, expl, st)

    doc.multiBuild(flow, canvasmaker=NumberedCanvas)
    # Page numbers are per-subject-PDF; the calendar always names the subject
    # alongside, so the reference is unambiguous.
    return out, doc.chapter_pages


def build_index_pdf(index: dict) -> Path:
    st = styles()
    out = paths.OUTPUT_PDF / "NEETPG_00_MASTER_INDEX.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    doc = ChapterDoc(str(out), pagesize=A4, title="NEET PG — Master Topic Index")
    doc.addPageTemplates([_frame_template("body")])

    flat = [t for s in index["subjects"].values()
            for sec in s["sections"] for t in sec["topics"]]
    flat.sort(key=lambda t: -t["highYield"])

    flow = _cover(
        "Master Topic Index",
        [f"{len(flat)} topics across {len(index['subjects'])} subjects",
         f"{index['totalTagged']} tagged previous-year questions",
         "Ranked by expected questions in your 2026 paper"],
        st,
    )

    flow.append(Paragraph("How this ranking works", st["h1"]))
    flow.append(Paragraph(
        "Every topic is scored on its share of each paper it appeared in, weighted by "
        "how much that paper predicts NEET PG 2026. Recent NEET PG and INI CET papers "
        "dominate; AIPGMEE (2012-2018) only breaks ties. The score reads as the number "
        "of questions to expect on that topic in a 200-question paper.", st["body"]))

    rows = [["Exam", "Year", "Questions", "Weight"]]
    for p in sorted(index["papers"], key=lambda p: -p["weight"]):
        rows.append([p["exam"], str(p["year"]), str(p["questions"]), f"{p['weight']:.2f}"])
    flow.append(data_table({"columns": rows[0], "rows": rows[1:],
                            "widths": [12, 6, 8, 6]}, st))

    flow.append(Paragraph("Top 100 topics", st["h1"]))
    rows = [["#", "Topic", "Subject", "Expected", "Tier", "PYQs", "Trend"]]
    for i, t in enumerate(flat[:100], start=1):
        rows.append([str(i), t["topic"], t["subject"], f"{t['highYield']:.2f}",
                     t["tier"], str(t["questionCount"]), t["trend"]])
    flow.append(data_table({"columns": rows[0], "rows": rows[1:],
                            "widths": [3, 29, 13, 8, 5, 5, 7]}, st))

    flow.append(PageBreak())
    flow.append(Paragraph("Every topic, by subject", st["h1"]))
    for subject, payload in sorted(index["subjects"].items(),
                                   key=lambda kv: -kv[1]["highYield"]):
        flow.append(Paragraph(
            f"{subject} &nbsp;&mdash;&nbsp; {payload['questionCount']} questions, "
            f"~{payload['highYield']:.1f} expected", st["h2"]))
        rows = [["Section", "Topic", "Expected", "Tier", "PYQs"]]
        for sec in payload["sections"]:
            for t in sec["topics"]:
                rows.append([sec["section"], t["topic"], f"{t['highYield']:.2f}",
                             t["tier"], str(t["questionCount"])])
        flow.append(data_table({"columns": rows[0], "rows": rows[1:],
                                "widths": [22, 30, 8, 4, 5]}, st))

    doc.multiBuild(flow, canvasmaker=NumberedCanvas)
    return out


def build_calendar_pdf(chapter_pages: dict[str, int] | None = None) -> Path | None:
    """One page per study day, with tick boxes and a page reference per topic."""
    if not paths.STUDY_CALENDAR.exists():
        return None
    with open(paths.STUDY_CALENDAR) as f:
        cal = json.load(f)
    chapter_pages = chapter_pages or {}

    st = styles()
    out = paths.OUTPUT_PDF / "NEETPG_00_CALENDAR.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    doc = ChapterDoc(str(out), pagesize=A4, title="NEET PG — 19-Day Study Calendar")
    doc.addPageTemplates([_frame_template("body")])

    hours = cal["dailyMinutes"] / 60
    flow = _cover("19-Day Study Calendar",
                  [f"{cal['start']} to {cal['exam']}",
                   f"{hours:g} hours a day",
                   "Tier A first, so falling behind costs the least"], st)

    flow.append(Paragraph("How to use this", st["h1"]))
    flow.append(Paragraph(
        "Each day mixes three or four subjects rather than blocking one subject per day — "
        "that matches the real paper and retains better. A fifth of each day is revisiting "
        "topics from three and nine days earlier; that is not padding, it is what stops you "
        "forgetting week one by the 30th. If you fall behind, drop tier C and read only the "
        "Must-know and Asked-again sections of tier B. Never skip tier A.", st["body"]))
    flow.append(PageBreak())

    for day in cal["days"]:
        head = (f"Day {day['day']} &nbsp;&mdash;&nbsp; {day['weekday']} {day['date']}"
                f" &nbsp;&mdash;&nbsp; {day['totalMinutes']} min")
        para = Paragraph(head, st["h1"])
        para._header = f"Day {day['day']} — {day['date']}"
        flow.append(para)

        if day.get("focus"):
            flow.append(Paragraph(rich(day["focus"]), st["body"]))

        for block in day["blocks"]:
            flow.append(Paragraph(
                f"{rich(block['subject'])} &nbsp;<font color='#5a6472'>"
                f"({block['minutes']} min)</font>", st["h2"]))
            rows = [["", "Topic", "Section", "Tier", "Min", "Page"]]
            for t in block["topics"]:
                page = chapter_pages.get(t["topicId"])
                rows.append(["☐", t["topic"], t["section"], t["tier"],
                             str(t["minutes"]), str(page) if page else "—"])
            flow.append(data_table({"columns": rows[0], "rows": rows[1:],
                                    "widths": [2, 31, 23, 5, 5, 5]}, st))

        if day["revisit"]:
            flow.append(Paragraph(
                f"Revisit &nbsp;<font color='#5a6472'>({day['revisitMinutes']} min)</font>",
                st["h2"]))
            names = ", ".join(t["topic"] for t in day["revisit"])
            flow.append(Paragraph(rich(names), st["small"]))
        flow.append(PageBreak())

    doc.multiBuild(flow, canvasmaker=NumberedCanvas)
    return out


def build_high_yield_pdf(index: dict, by_id: dict, expl: dict) -> Path | None:
    chapters = [c for c in load_chapters() if c.get("tier") == "A"]
    if not chapters:
        return None
    st = styles()
    chapters.sort(key=lambda c: -c["highYield"])
    out = paths.OUTPUT_PDF / "NEETPG_HIGH_YIELD_ONLY.pdf"
    doc = ChapterDoc(str(out), pagesize=A4, title="NEET PG — High Yield Only")
    doc.addPageTemplates([_frame_template("body")])
    flow = _cover("High Yield Only",
                  [f"{len(chapters)} tier-A topics across every subject",
                   "The ones to read on 28-29 August"], st)
    flow += _toc(st)
    for ch in chapters:
        flow += chapter_flowables(ch, by_id, expl, st)
    doc.multiBuild(flow, canvasmaker=NumberedCanvas)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--subject")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--index", action="store_true")
    ap.add_argument("--high-yield", action="store_true")
    ap.add_argument("--calendar", action="store_true")
    args = ap.parse_args()

    register_fonts()
    with open(paths.TOPIC_INDEX) as f:
        index = json.load(f)
    by_id = {r["id"]: r for r in dataio.load_master()}
    for rec in json.load(open(paths.PUBLIC_QUESTIONS)):   # image fields live only here
        if rec["id"] in by_id and ("imageUrl" in rec or "imageUrls" in rec):
            by_id[rec["id"]] = {**by_id[rec["id"]],
                                **{k: rec[k] for k in ("imageUrl", "imageUrls") if k in rec}}
    expl = dataio.load_explanations()

    pages: dict[str, int] = {}
    targets = ([args.subject] if args.subject
               else sorted(index["subjects"]) if args.all else [])
    for subject in targets:
        built = build_subject_pdf(subject, index, by_id, expl)
        if built:
            out, subject_pages = built
            pages.update(subject_pages)
            print(f"  {subject:26s} -> {out.name} ({len(subject_pages)} chapters)")
        else:
            print(f"  {subject:26s} -> no chapters yet")
    if args.index:
        print(f"  master index -> {build_index_pdf(index).name}")
    if args.high_yield:
        out = build_high_yield_pdf(index, by_id, expl)
        print(f"  high yield -> {out.name if out else 'no tier-A chapters yet'}")
    if args.calendar:
        # Rendered last so every chapter's start page is known.
        out = build_calendar_pdf(pages)
        print(f"  calendar -> {out.name if out else 'no calendar built yet'}"
              f" ({len(pages)} page references)")


if __name__ == "__main__":
    main()
