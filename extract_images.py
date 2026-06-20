#!/usr/bin/env python3
"""
NEET PG PDF Image Extractor
============================
Extracts real question images from all NEET PG PDFs and:
1. Saves them as PNG files in data/images/<year>_s<shift>/
2. Produces data/extracted/image_map.json  →  { questionId: "relative/path.png" }

How it works:
  - Format A (2012-2020): one question per page → images on that page belong to that question
  - Format D (2024):      text-based → find nearest "Ques N." above each image on the page
  - Filters out logos/trackers by size (skips 240x34 header, 1x1 pixel trackers)

Run:
    python3 extract_images.py

Then upload images to Firebase Storage with:
    python3 upload_images_firebase.py   (generated separately after review)
"""

import re
import json
import os
from pathlib import Path

import fitz  # PyMuPDF

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

PDF_DIR    = Path("data/pdfs")
IMAGE_DIR  = Path("data/images")
OUTPUT_MAP = Path("data/extracted/image_map.json")

IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# Image size filters:  skip anything that looks like a logo or tracker
LOGO_SIZES  = {(240, 34), (480, 68)}   # FirstRanker header (1x and 2x)
MIN_WIDTH   = 80    # px — skip tiny decorative icons
MIN_HEIGHT  = 60    # px
MAX_WIDTH   = 2000  # sanity cap

# Map each PDF to (year, shift, format)
# format A: one question per page
# format D: multiple questions per page (text scan needed)
PDF_CONFIG = [
    ("FR_neet-pg-2012-question-paper-with-answers.pdf",    2012, 1, "A"),
    ("FR_neet-pg-2013-question-paper-with-answers.pdf",    2013, 1, "A"),
    ("FR_neet-pg-2014-question-paper-with-answers.pdf",    2014, 1, "A"),
    ("FR_neet-pg-2015-question-paper-with-answers.pdf",    2015, 1, "A"),
    ("FR_neet-pg-2016-question-paper-with-answers.pdf",    2016, 1, "A"),
    ("FR_neet-pg-2017-question-paper-with-answers.pdf",    2017, 1, "A"),
    ("FR_neet-pg-2018-question-paper-with-answers.pdf",    2018, 1, "A"),
    ("FR_neet-pg-2019-question-paper-with-answers.pdf",    2019, 1, "A"),
    ("FR_neet-pg-2020-question-paper-with-answers.pdf",    2020, 1, "A"),
    # 2021 is scanned (no text layer) — skipped
    ("FR_neet-pg-2022-question-paper-with-solutions.pdf",  2022, 1, "C"),
    ("FR_neet-pg-2023-question-paper-with-solutions.pdf",  2023, 1, "C"),
    ("FR_neet-pg-2024-shift-1-question-paper.pdf",         2024, 1, "D"),
    ("FR_neet-pg-2024-shift-2-question-paper.pdf",         2024, 2, "D"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_question_id(year: int, shift: int, q_num: int) -> str:
    return f"neetpg-{year}-s{shift}-q{q_num:04d}"


def is_real_image(w: int, h: int) -> bool:
    """Return True if the image dimensions look like a real question image."""
    if (w, h) in LOGO_SIZES:
        return False
    if w < MIN_WIDTH or h < MIN_HEIGHT or w > MAX_WIDTH:
        return False
    return True


def save_image(doc: fitz.Document, xref: int, out_path: Path) -> bool:
    """Extract image by xref and save to disk. Returns True on success."""
    try:
        base = doc.extract_image(xref)
        ext  = base["ext"]          # "png", "jpeg", etc.
        data = base["image"]
        # Always save as PNG for consistency
        final_path = out_path.with_suffix(".png")
        if ext in ("png", "jpeg", "jpg"):
            # For non-PNG formats, re-render via pixmap for uniform output
            if ext != "png":
                pix = fitz.Pixmap(doc, xref)
                if pix.n > 4:          # CMYK → convert to RGB
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                pix.save(str(final_path))
            else:
                with open(str(final_path), "wb") as f:
                    f.write(data)
        else:
            return False  # unsupported format
        return True
    except Exception as e:
        print(f"    [warn] Failed to save image xref={xref}: {e}")
        return False


# ---------------------------------------------------------------------------
# Format A extractor  (2012–2020: one question per page)
# ---------------------------------------------------------------------------

def extract_format_a(pdf_path: Path, year: int, shift: int) -> dict:
    """
    Each page = one question. Parse question number from start of page text.
    Any real image on that page belongs to that question.
    Returns: { questionId: [image_paths] }
    """
    mapping = {}
    out_dir = IMAGE_DIR / f"{year}_s{shift}"
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))

    for page_num, page in enumerate(doc):
        text = page.get_text()
        if not text:
            continue

        # Extract question number — strip watermark URLs (e.g. www.FirstRanker.com) first
        text_clean = re.sub(r'^\s*\S+\.\S+\s*', '', text, flags=re.MULTILINE).lstrip()
        m = re.match(r'^\s*(\d+)[.)]\s', text_clean)
        if not m:
            continue
        q_num = int(m.group(1))
        q_id  = make_question_id(year, shift, q_num)

        images = page.get_images(full=True)
        saved  = []

        for img_index, img in enumerate(images):
            xref = img[0]
            base = doc.extract_image(xref)
            w, h = base["width"], base["height"]

            if not is_real_image(w, h):
                continue

            filename  = f"q{q_num:04d}_{img_index}.png"
            out_path  = out_dir / filename
            rel_path  = f"images/{year}_s{shift}/{filename}"

            if save_image(doc, xref, out_path):
                saved.append(rel_path)

        if saved:
            mapping[q_id] = saved

    doc.close()
    return mapping


# ---------------------------------------------------------------------------
# Format D extractor  (2024: multiple questions per page)
# ---------------------------------------------------------------------------

def extract_format_d(pdf_path: Path, year: int, shift: int) -> dict:
    """
    Multiple questions per page. For each page, find question number markers
    near each image using text position (bounding boxes).
    Returns: { questionId: [image_paths] }
    """
    mapping = {}
    out_dir = IMAGE_DIR / f"{year}_s{shift}"
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))

    for page_num, page in enumerate(doc):
        # Get all text spans with their bounding boxes
        blocks = page.get_text("dict")["blocks"]

        # Build list of (y_top, question_number) for all "Ques N." markers on page
        q_markers = []
        for block in blocks:
            if block.get("type") != 0:  # text block
                continue
            for line in block.get("lines", []):
                line_text = " ".join(s["text"] for s in line.get("spans", []))
                m = re.search(r'Ques\s+(\d+)\.', line_text)
                if m:
                    y_top = line["bbox"][1]
                    q_markers.append((y_top, int(m.group(1))))

        q_markers.sort(key=lambda x: x[0])   # sort top→bottom

        # Match images to their bounding boxes on the page.
        # get_image_info() uses non-sequential 'number' keys so we can't index-match.
        # Instead we correlate by (width, height) — good enough since logos are filtered out.
        img_infos = page.get_image_info(hashes=False)
        images    = page.get_images(full=True)

        # Map (w, h) → list of bboxes (multiple images can share same size)
        size_to_bboxes: dict = {}
        for info in img_infos:
            key = (info["width"], info["height"])
            size_to_bboxes.setdefault(key, []).append(info["bbox"])

        used_bboxes: set = set()

        for img in images:
            xref = img[0]
            base = doc.extract_image(xref)
            w, h = base["width"], base["height"]

            if not is_real_image(w, h):
                continue

            # Pick the first unused bbox for this size
            bboxes = size_to_bboxes.get((w, h), [])
            bbox   = None
            for b in bboxes:
                key = tuple(b)
                if key not in used_bboxes:
                    bbox = b
                    used_bboxes.add(key)
                    break
            if not bbox:
                continue

            img_y_top = bbox[1]   # top of image on page

            # Find the nearest "Ques N." above this image
            q_num = None
            for (q_y, q_n) in reversed(q_markers):
                if q_y <= img_y_top:
                    q_num = q_n
                    break
            if q_num is None and q_markers:
                q_num = q_markers[0][1]   # fallback: first question on page
            if q_num is None:
                continue

            q_id     = make_question_id(year, shift, q_num)
            filename = f"q{q_num:04d}_p{page_num+1}_{xref}.png"
            out_path = out_dir / filename
            rel_path = f"images/{year}_s{shift}/{filename}"

            if save_image(doc, xref, out_path):
                if q_id not in mapping:
                    mapping[q_id] = []
                if rel_path not in mapping[q_id]:
                    mapping[q_id].append(rel_path)

    doc.close()
    return mapping


# ---------------------------------------------------------------------------
# Format C extractor  (2022-2023: similar to D but diff markers)
# ---------------------------------------------------------------------------

def extract_format_c(pdf_path: Path, year: int, shift: int) -> dict:
    """
    2022-2023 format: 'Ques No: N' markers.
    """
    mapping = {}
    out_dir = IMAGE_DIR / f"{year}_s{shift}"
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))

    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]

        q_markers = []
        for block in blocks:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                line_text = " ".join(s["text"] for s in line.get("spans", []))
                m = re.search(r'Ques\s*No[:\s]+(\d+)', line_text, re.IGNORECASE)
                if m:
                    y_top = line["bbox"][1]
                    q_markers.append((y_top, int(m.group(1))))

        q_markers.sort(key=lambda x: x[0])

        img_infos = page.get_image_info(hashes=False)
        images    = page.get_images(full=True)

        size_to_bboxes: dict = {}
        for info in img_infos:
            key = (info["width"], info["height"])
            size_to_bboxes.setdefault(key, []).append(info["bbox"])

        used_bboxes: set = set()

        for img in images:
            xref = img[0]
            base = doc.extract_image(xref)
            w, h = base["width"], base["height"]

            if not is_real_image(w, h):
                continue

            bboxes = size_to_bboxes.get((w, h), [])
            bbox   = None
            for b in bboxes:
                key = tuple(b)
                if key not in used_bboxes:
                    bbox = b
                    used_bboxes.add(key)
                    break
            if not bbox:
                continue

            img_y_top = bbox[1]
            q_num = None
            for (q_y, q_n) in reversed(q_markers):
                if q_y <= img_y_top:
                    q_num = q_n
                    break
            if q_num is None and q_markers:
                q_num = q_markers[0][1]
            if q_num is None:
                continue

            q_id     = make_question_id(year, shift, q_num)
            filename = f"q{q_num:04d}_p{page_num+1}_{xref}.png"
            out_path = out_dir / filename
            rel_path = f"images/{year}_s{shift}/{filename}"

            if save_image(doc, xref, out_path):
                if q_id not in mapping:
                    mapping[q_id] = []
                if rel_path not in mapping[q_id]:
                    mapping[q_id].append(rel_path)

    doc.close()
    return mapping


EXTRACTORS = {
    "A": extract_format_a,
    "C": extract_format_c,
    "D": extract_format_d,
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run():
    full_map = {}   # questionId → [relative_image_paths]
    stats = {}

    for filename, year, shift, fmt in PDF_CONFIG:
        pdf_path = PDF_DIR / filename
        if not pdf_path.exists():
            print(f"  SKIP: {filename} not found")
            continue

        print(f"\n[{year} S{shift}] Extracting images (format {fmt})...")

        extractor = EXTRACTORS.get(fmt)
        if not extractor:
            print(f"  SKIP: No extractor for format {fmt}")
            continue

        try:
            mapping = extractor(pdf_path, year, shift)
        except Exception as e:
            print(f"  ERROR: {e}")
            mapping = {}

        count = sum(len(v) for v in mapping.values())
        stats[f"{year}-s{shift}"] = {"questions_with_images": len(mapping), "total_images": count}
        print(f"  → {len(mapping)} questions with images ({count} total image files)")
        full_map.update(mapping)

    # Save the full map
    OUTPUT_MAP.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_MAP, "w", encoding="utf-8") as f:
        json.dump(full_map, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Image map saved → {OUTPUT_MAP}")
    print(f"Total questions with images: {len(full_map)}")
    print(f"Total image files: {sum(len(v) for v in full_map.values())}")
    print(f"\nPer-year breakdown:")
    for k, v in stats.items():
        print(f"  {k}: {v['questions_with_images']} questions, {v['total_images']} images")

    print(f"\nNext step:")
    print(f"  Review images in data/images/")
    print(f"  Then run: python3 upload_images_firebase.py")


if __name__ == "__main__":
    run()
