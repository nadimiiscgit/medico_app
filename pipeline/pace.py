"""How long a topic actually takes to study.

The first version of this estimate was a function of the high-yield score alone:

    est_minutes = clamp(6 + 16 * high_yield, 8, 40)

It never looked at how long the chapter was or how many questions the topic carried,
so Cardiac Arrhythmias — 2,058 words of prose, 6 tables totalling 41 rows, 17
must-know lines and 32 MCQs with explanations — was budgeted 23 minutes. Measured
against the material it is about 75. Across all 582 topics the old estimate was 3.7
times too low, which is what made an impossible plan look like it fitted.

This module estimates from the material instead:

    minutes = words/wpm + rows*row_sec + must_know*mk_sec + selected_pyqs*pyq_min

Chapter figures are read from the generated chapters where they exist, and fall back
to per-tier defaults where they do not, so the estimate sharpens by itself as more
chapters are written.

Solving questions is 65% of the total load, so `selected_pyqs` is also where the
scheduling decision lives — see `select_pyq_ids`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from . import paths


@dataclass(frozen=True)
class Pace:
    """One person's working speed. Every figure is overridable from the CLI."""

    wpm: float = 130.0        # dense medical prose, studying rather than skimming
    row_seconds: float = 12.0  # absorbing one comparison-table row
    mk_seconds: float = 15.0   # one must-know line
    pyq_minutes: float = 1.5   # solve an MCQ and read its explanation


DEFAULT = Pace()

# Used where a chapter has not been written yet. Medians of the chapters that exist
# today are 2,098 words / 39 rows / 15 must-know, all tier A; B and C follow the
# word targets the chapter prompt asks for, scaled proportionally.
TIER_DEFAULTS = {
    "A": {"words": 2100, "rows": 39, "mustKnow": 15},
    "B": {"words": 1300, "rows": 24, "mustKnow": 10},
    "C": {"words": 550, "rows": 10, "mustKnow": 6},
}

# How much of a chapter you read when a tier is reduced to its Must-know list.
MUSTKNOW_ONLY_FRACTION = 0.25

SCOPES = ("recent", "all", "none")


def _chapter_path(topic_id: str, subject: str) -> "paths.Path":
    slug = subject.lower().replace(" ", "-").replace("&", "").replace("--", "-")
    return paths.CHAPTERS / slug / f"{topic_id}.json"


def chapter_shape(topic: dict, subject: str) -> dict:
    """Words, table rows and must-know count for a topic's chapter.

    Falls back to the tier default when the chapter has not been generated.
    """
    tier = topic.get("tier", "C")
    path = _chapter_path(topic["topicId"], subject)
    if not path.exists():
        # Chapter filenames are keyed by topic id, so a rglob is a cheap fallback
        # when the subject slug does not match the directory exactly.
        matches = list(paths.CHAPTERS.rglob(f"{topic['topicId']}.json")) \
            if paths.CHAPTERS.exists() else []
        if not matches:
            return {**TIER_DEFAULTS[tier], "measured": False}
        path = matches[0]

    with open(path) as f:
        chapter = json.load(f)
    words = sum(len(s.get("body", "").split())
                for s in chapter.get("sections", []) if s.get("type") == "concept")
    rows = sum(len(s.get("rows") or []) for s in chapter.get("sections", []))
    return {
        "words": words or TIER_DEFAULTS[tier]["words"],
        "rows": rows,
        "mustKnow": len(chapter.get("mustKnow") or []),
        "measured": True,
    }


def select_pyq_ids(topic: dict, by_id: dict, scope: str = "recent") -> list[str]:
    """Which of a topic's questions the calendar actually schedules.

    `recent` keeps every NEET PG and INI CET question from 2019 on, plus one
    representative per repeat cluster — 2,028 of 10,963 across the corpus. Those are
    the questions the ranking says predict the paper; the rest are near-duplicates
    from AIPGMEE years already discounted to near zero, and stay in the PDFs as
    extra practice rather than being scheduled.
    """
    ids = topic.get("questionIds") or []
    if scope == "none":
        return []
    if scope == "all":
        return list(ids)

    picked = [q for q in ids
              if (rec := by_id.get(q)) and
              (rec.get("exam") in ("NEET PG", "INI CET") or int(rec.get("year", 0)) >= 2019)]
    seen = set(picked)
    for cluster in topic.get("repeatClusters") or []:
        for qid in cluster:
            if qid not in seen and qid in by_id:
                picked.append(qid)
                seen.add(qid)
                break
    return picked


def estimate(topic: dict, subject: str, by_id: dict, *,
             pace: Pace = DEFAULT, scope: str = "recent",
             reduced: bool = False) -> dict:
    """Minutes for one topic, split into reading and solving.

    `reduced` means this tier is being read as its Must-know list only.
    """
    shape = chapter_shape(topic, subject)
    fraction = MUSTKNOW_ONLY_FRACTION if reduced else 1.0

    read = (shape["words"] * fraction / pace.wpm
            + shape["rows"] * fraction * pace.row_seconds / 60
            + shape["mustKnow"] * pace.mk_seconds / 60)

    pyq_ids = [] if reduced else select_pyq_ids(topic, by_id, scope)
    solve = len(pyq_ids) * pace.pyq_minutes

    return {
        "readMinutes": max(1, round(read)),
        "solveMinutes": round(solve),
        "minutes": max(2, round(read + solve)),
        "selectedPyqIds": pyq_ids,
        "measured": shape["measured"],
        "words": shape["words"],
    }


def add_pace_args(parser) -> None:
    parser.add_argument("--wpm", type=float, default=DEFAULT.wpm,
                        help="reading speed for dense medical prose (default 130)")
    parser.add_argument("--pyq-minutes", type=float, default=DEFAULT.pyq_minutes,
                        help="minutes to solve one MCQ and read its explanation")
    parser.add_argument("--row-seconds", type=float, default=DEFAULT.row_seconds)
    parser.add_argument("--mk-seconds", type=float, default=DEFAULT.mk_seconds)


def pace_from_args(args) -> Pace:
    return Pace(wpm=args.wpm, row_seconds=args.row_seconds,
                mk_seconds=args.mk_seconds, pyq_minutes=args.pyq_minutes)
