"""Parsers for memory-based recall papers.

Neither NBE (NEET PG) nor AIIMS (INI CET) releases question papers, so every
recent paper only exists as a memory-based recall compiled by students and
coaching institutes. These come in two shapes, and both are worth having for
different reasons:

  FULL    question + four options + answer letter. Usable as a real Question.
  PARTIAL question/scenario + answer, no options. Not usable as an MCQ, but it
          still names what the topic was — which is exactly the signal topic
          prioritisation needs, and it comes from the most recent papers.

Everything parsed here is marked `sourceConfidence: "memory_based"` so nothing
downstream mistakes it for an official paper.
"""
from __future__ import annotations

import html
import re
import unicodedata

# Corpus subject names differ slightly from what the recall sources use.
SUBJECT_ALIASES = {
    "orthopedics": "Orthopaedics",
    "orthopaedics": "Orthopaedics",
    "obstetrics and gynaecology": "Obstetrics & Gynaecology",
    "obstetrics and gynecology": "Obstetrics & Gynaecology",
    "obg": "Obstetrics & Gynaecology",
    "obs and gynae": "Obstetrics & Gynaecology",
    "pediatrics": "Paediatrics",
    "paediatrics": "Paediatrics",
    "anesthesia": "Anaesthesia",
    "anaesthesia": "Anaesthesia",
    "psm": "Community Medicine",
    "community medicine": "Community Medicine",
    "forensic medicine": "Forensic Medicine",
    "forensic": "Forensic Medicine",
    "skin": "Dermatology",
    "dermatology": "Dermatology",
    "ent": "ENT",
    "radiology": "Radiology",
    "radiodiagnosis": "Radiology",
    "ophthalmology": "Ophthalmology",
    "medicine": "Medicine",
    "general medicine": "Medicine",
    "surgery": "Surgery",
    "general surgery": "Surgery",
    "anatomy": "Anatomy",
    "physiology": "Physiology",
    "biochemistry": "Biochemistry",
    "pathology": "Pathology",
    "pharmacology": "Pharmacology",
    "microbiology": "Microbiology",
    "psychiatry": "Psychiatry",
    "immunology": "Microbiology",
    "genetics": "Biochemistry",
    "parasitology": "Microbiology",
}

ANSWER_RE = re.compile(r"Answer\s*[–—\-:]*\s*\(?([A-D])\)?", re.IGNORECASE)
Q_RE = re.compile(r"^Q\s*[\.\)]?\s*(\d{1,3})\s*[\.\)]\s*(.*)$", re.IGNORECASE)

# Boilerplate that survives HTML-to-text conversion and must never become an option.
JUNK_RE = re.compile(
    r"^(download|click here|read more|also read|subscribe|share|whatsapp|telegram|"
    r"facebook|twitter|copyright|all rights reserved|table of contents|faq|"
    r"frequently asked|related (blogs?|articles?)|previous|next|home|blog)\b",
    re.IGNORECASE,
)


def normalise_subject(raw: str) -> str | None:
    key = re.sub(r"[^a-z& ]+", " ", raw.lower()).strip()
    key = re.sub(r"\s+", " ", key)
    return SUBJECT_ALIASES.get(key)


# Longest first so "Community Medicine" is not shadowed by "Medicine".
_ALIAS_BY_LENGTH = sorted(SUBJECT_ALIASES, key=len, reverse=True)


def subject_in(line: str) -> str | None:
    """Find a subject named anywhere in a heading.

    Recall blogs are inconsistent about where the subject sits: one year writes
    'Anatomy NEET PG 2025 Recall Questions', the next writes
    'INI-CET Anatomy 2026 Recall Questions'. Position is not dependable, so the
    heading is scanned for any known subject name instead.
    """
    key = re.sub(r"[^a-z& ]+", " ", line.lower())
    key = " " + re.sub(r"\s+", " ", key).strip() + " "
    for alias in _ALIAS_BY_LENGTH:
        if f" {alias} " in key:
            return SUBJECT_ALIASES[alias]
    return None


def clean_text(s: str) -> str:
    """Collapse whitespace and normalise the punctuation reportlab can't render."""
    s = unicodedata.normalize("NFKC", s)
    for bad, good in (
        ("–", "-"), ("—", "-"), ("‘", "'"), ("’", "'"),
        ("“", '"'), ("”", '"'), (" ", " "), ("→", "->"),
        ("↑", " increased "), ("↓", " decreased "), ("×", "x"),
        ("≥", ">="), ("≤", "<="), ("…", "..."),
    ):
        s = s.replace(bad, good)
    return re.sub(r"\s+", " ", s).strip()


def html_to_lines(raw_html: str) -> list[str]:
    body = re.sub(r"(?is)<(script|style|nav|footer|header|form)[^>]*>.*?</\1>", " ", raw_html)
    body = re.sub(r"(?is)<br\s*/?>", "\n", body)
    text = html.unescape(re.sub(r"(?s)<[^>]+>", "\n", body))
    out = []
    for line in text.split("\n"):
        line = clean_text(line)
        if line:
            out.append(line)
    return out


def parse_subject_blog(raw_html: str, header_pattern: str) -> list[dict]:
    """Parse a recall blog laid out as: subject header, then Qn / options / Answer.

    `header_pattern` matches the per-subject heading, e.g. r'INI-?CET 2025 Recall'.
    Options are unlabelled lines between the stem and the answer. Where a question
    carries a match-the-following list, the real choices are the last four lines,
    which is why the tail is taken rather than the head.
    """
    lines = html_to_lines(raw_html)
    hdr = re.compile(header_pattern, re.IGNORECASE)

    # Locate subject sections: a header line whose leading words name a subject.
    sections: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        if not hdr.search(line):
            continue
        # Some years put the subject in the heading ('Anatomy NEET PG 2025
        # Recall Questions'), others put it on its own line just above it. The
        # length guard keeps option text that merely mentions a subject from
        # being mistaken for a heading.
        subject = subject_in(line)
        if not subject and i and len(lines[i - 1]) <= 40:
            subject = subject_in(lines[i - 1])
        if subject:
            sections.append((i, subject))
    if not sections:
        return []

    parsed: list[dict] = []
    for idx, (start, subject) in enumerate(sections):
        end = sections[idx + 1][0] if idx + 1 < len(sections) else len(lines)
        parsed.extend(_parse_section(lines[start + 1:end], subject))
    return parsed


def _parse_section(lines: list[str], subject: str) -> list[dict]:
    # Split the section into per-question blocks.
    starts = [i for i, l in enumerate(lines) if Q_RE.match(l)]
    out = []
    for n, s in enumerate(starts):
        e = starts[n + 1] if n + 1 < len(starts) else len(lines)
        block = lines[s:e]
        rec = _parse_block(block, subject)
        if rec:
            out.append(rec)
    return out


def _degenerate(tail: list[str]) -> bool:
    """True when the 'options' are just image labels rather than real answer text.

    Image-based questions in these recalls often render as a bare A / B / C / D
    list because the choices were pictures. Keeping those would put four
    meaningless single letters into the corpus, so they are treated as
    options-not-recoverable instead.
    """
    stripped = [re.sub(r"[^A-Za-z0-9]", "", t).upper() for t in tail]
    if stripped == ["A", "B", "C", "D"] or stripped == ["1", "2", "3", "4"]:
        return True
    return all(len(t) <= 2 for t in stripped)


def _parse_block(block: list[str], subject: str) -> dict | None:
    m = Q_RE.match(block[0])
    if not m:
        return None
    number = int(m.group(1))
    stem_parts = [m.group(2)] if m.group(2) else []

    # Find where the answer marker starts; everything before it is stem + options.
    answer = None
    ans_at = len(block)
    joined_tail = ""
    for i in range(1, len(block)):
        if re.match(r"^Answer\b", block[i], re.IGNORECASE):
            ans_at = i
            joined_tail = " ".join(block[i:i + 3])
            am = ANSWER_RE.search(joined_tail)
            answer = am.group(1).upper() if am else None
            break
    if answer is None:
        return None

    middle = [l for l in block[1:ans_at] if not JUNK_RE.match(l)]

    # A stem can wrap onto continuation lines. Anything before the option run is stem.
    options: dict[str, str] = {}
    if len(middle) >= 4:
        tail = middle[-4:]
        # Reject a "tail" that is obviously prose continuation rather than choices.
        if all(len(t) <= 200 for t in tail) and not _degenerate(tail):
            options = dict(zip("ABCD", tail))
            stem_parts += middle[:-4]
        else:
            stem_parts += middle
    else:
        stem_parts += middle

    stem = clean_text(" ".join(stem_parts))
    if not stem:
        return None

    return {
        "number": number,
        "subject": subject,
        "question": stem,
        "options": options,
        "correctAnswer": answer,
        "complete": len(options) == 4,
    }


def _lines_of(words: list[dict]) -> list[list[dict]]:
    """Group a page's words into visual lines by their `top` coordinate."""
    buckets: dict[float, list[dict]] = {}
    for w in words:
        buckets.setdefault(round(w["top"], 1), []).append(w)
    return [sorted(buckets[k], key=lambda w: w["x0"]) for k in sorted(buckets)]


# The document uses exactly two table geometries. Detecting edges from the text
# alone drifts whenever a subject cell wraps, which silently shifts every field
# one column right, so pages are matched against these instead.
PGM_LAYOUTS = (
    ("numbered", [77.0, 189.0, 301.0, 412.0]),    # Q.No | Subject | Scenario | Answer
    ("plain", [77.0, 227.0, 377.0]),              # Subject | Scenario | Answer
)

# Header and section-divider text that is not a question.
PGM_JUNK_RE = re.compile(
    r"^(by\s+pg|pg\s*masters|masters|\(?pg_masters|topic\s*/\s*subject|"
    r"question\s*/\s*scenario|answer|\d+\s*-\s*\d+\s*\(?final|final\s*round|round\s*\)?)",
    re.IGNORECASE,
)


def _pick_layout(lines: list[list[dict]]) -> list[float]:
    """Choose this page's layout.

    Row numbers are the decisive signal: the numbered table prints a bare
    integer in the leftmost column on every row, and the unnumbered table never
    does. Scoring cell-start positions alone gets the transition page wrong,
    because both geometries partly fit it.
    """
    numbered_edges = PGM_LAYOUTS[0][1]
    plain_edges = PGM_LAYOUTS[1][1]

    row_numbers = sum(
        1 for line in lines
        if line and abs(line[0]["x0"] - numbered_edges[0]) <= 8 and line[0]["text"].isdigit()
    )
    if row_numbers >= 2:
        return numbered_edges

    # Otherwise fall back to which geometry explains more cell starts.
    starts = []
    for line in lines:
        prev_x1 = None
        for w in line:
            if prev_x1 is None or w["x0"] - prev_x1 > 12:
                starts.append(w["x0"])
            prev_x1 = w["x1"]
    hits = sum(1 for x in starts if any(abs(x - e) <= 8 for e in plain_edges))
    return plain_edges if starts and hits / len(starts) >= 0.5 else []


def parse_pgmasters_table(pdf_path: str) -> list[dict]:
    """Parse the PG Masters NEET PG recall table.

    The PDF draws no ruling lines, so pdfplumber's table detection finds nothing
    and plain text extraction interleaves the columns. Cells are recovered from
    word x-positions instead.

    The document contains two different tables with different geometry — a
    numbered 4-column one (Q.No | Topic/Subject | Scenario | Answer) and an
    unnumbered 3-column one (Topic/Subject | Scenario | Answer) — so columns are
    detected per page rather than assumed, and a row break is a cell starting in
    the leftmost column after a vertical gap wider than normal line spacing.

    Every row comes back PARTIAL: this layout has no options at all. Its value
    is the topic column, which states outright what each question tested.
    """
    import pdfplumber

    rows: list[dict] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = [
                {"top": float(w["top"]), "x0": float(w["x0"]),
                 "x1": float(w["x1"]), "text": w["text"]}
                for w in page.extract_words()
            ]
            if not words:
                continue
            lines = _lines_of(words)
            edges = _pick_layout(lines)
            if len(edges) < 3:
                continue
            rows.extend(_rows_from_page(lines, edges, edges is PGM_LAYOUTS[0][1]))
    return rows


def _rows_from_page(lines: list[list[dict]], edges: list[float],
                    numbered_page: bool) -> list[dict]:
    """Slice one page's lines into records using the page's column edges."""
    def column(x0: float) -> int:
        idx = 0
        for i, e in enumerate(edges):
            if x0 >= e - 6:
                idx = i
        return idx

    # Normal line spacing on these pages is ~14.5pt; a larger step means a new row.
    tops = [line[0]["top"] for line in lines]
    gaps = sorted(round(b - a, 1) for a, b in zip(tops, tops[1:]) if b > a)
    line_gap = gaps[len(gaps) // 2] if gaps else 15.0
    row_break = line_gap * 1.8

    groups: list[list[list[dict]]] = []
    prev_top = None
    for line in lines:
        starts_left = column(line[0]["x0"]) == 0
        big_gap = prev_top is not None and (line[0]["top"] - prev_top) > row_break
        if starts_left and (not groups or big_gap or prev_top is None):
            groups.append([line])
        elif groups:
            groups[-1].append(line)
        prev_top = line[0]["top"]

    out: list[dict] = []
    for group in groups:
        cells: dict[int, list[str]] = {}
        for line in group:
            for w in line:
                cells.setdefault(column(w["x0"]), []).append(w["text"])

        col0 = clean_text(" ".join(cells.get(0, [])))
        number = int(col0) if col0.isdigit() else None
        # Numbered layout shifts every field one column right.
        off = 1 if number is not None else 0
        subject_raw = col0 if number is None else clean_text(" ".join(cells.get(1, [])))
        question = clean_text(" ".join(cells.get(1 + off, [])))
        answer = clean_text(" ".join(cells.get(2 + off, [])))

        if not question or len(question) < 5:
            continue
        if PGM_JUNK_RE.match(question) or PGM_JUNK_RE.match(subject_raw):
            continue
        # The second table starts partway down the last numbered page. Its rows
        # get sliced with the wrong geometry and come out interleaved, but they
        # are identifiable: on a numbered page every real row carries a number.
        if numbered_page and number is None:
            continue
        out.append({
            "number": number,
            # The topic column is often "Pathology / Endocrinology" — the first
            # part names the subject, the rest is a topic hint worth keeping.
            "subject": normalise_subject(subject_raw.split("/")[0]) or "",
            "subjectRaw": subject_raw,
            "question": question,
            "answer": answer,
            "options": {},
            "complete": False,
        })
    return out
