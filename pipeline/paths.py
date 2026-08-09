"""Canonical, repo-relative paths for the whole pipeline.

Nothing in `pipeline/` may hardcode an absolute path. Import from here instead.
"""
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# --- source of truth -------------------------------------------------------
QUESTIONS = REPO / "data/extracted/questions.json"

# --- app-served copies -----------------------------------------------------
PUBLIC = REPO / "medico-app/public"
PUBLIC_QUESTIONS = PUBLIC / "questions.json"
EXPLANATIONS = PUBLIC / "explanations.json"
QUESTION_IMAGES = PUBLIC / "question-images"

# --- pipeline working area -------------------------------------------------
PDFS = REPO / "data/pdfs"
TOPICS = REPO / "data/topics"
TAXONOMY = TOPICS / "taxonomy.json"
QUESTION_TOPICS = TOPICS / "question_topics.json"
TOPIC_INDEX = TOPICS / "topic_index.json"
TOPIC_INDEX_SLIM = TOPICS / "topic_index.slim.json"
STUDY_CALENDAR = TOPICS / "study_calendar.json"
CHAPTERS = TOPICS / "chapters"
PACKETS = TOPICS / "packets"
RETURNS = TOPICS / "returns"

BACKUPS = REPO / "data/backups"
OUTPUT_PDF = REPO / "output/pdf"
FONTS = Path(__file__).resolve().parent / "fonts"

DOCS = REPO / "docs"


def ensure_dirs() -> None:
    """Create every pipeline-owned directory. Safe to call repeatedly."""
    for d in (
        PDFS, TOPICS, CHAPTERS, PACKETS, RETURNS, BACKUPS, OUTPUT_PDF, FONTS, DOCS,
        PACKETS / "tag", PACKETS / "chapter",
        RETURNS / "tag", RETURNS / "chapter",
    ):
        d.mkdir(parents=True, exist_ok=True)
