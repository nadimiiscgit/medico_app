"""Phase 4 — build chapter work packets and validate what comes back.

One chapter per topic. Depth scales with the topic's high-yield score, because
~550 full-length chapters is more than anyone can read in nineteen days:

    tier A  >= 1.0 expected questions   1800-2500 words   deep teaching chapter
    tier B  0.4 - 1.0                   1000-1500 words   standard chapter
    tier C  < 0.4                        400- 600 words   compact fact sheet

Each packet carries every PYQ for its topic verbatim, with the explanation, so
the chapter is written from what the exam actually asked rather than from
recall. It also carries the neighbouring topic names, which is what stops 550
chapters from re-explaining the brachial plexus seven times.

Chapters come back as structured JSON rather than prose markdown so the PDF
renderer is deterministic and the output can be checked mechanically. The
question bank stores ids only — the renderer joins against the corpus, so the
questions printed in your PDF are always the verbatim originals and never an
LLM's re-transcription of them.

Usage:
    python3 -m pipeline.chapters --emit --subject Pharmacology
    python3 -m pipeline.chapters --emit --tier A
    python3 -m pipeline.chapters --ingest
    python3 -m pipeline.chapters --status
"""
from __future__ import annotations

import argparse
import collections
import json
import re

from . import dataio, paths

PACKET_DIR = paths.PACKETS / "chapter"
RETURN_DIR = paths.RETURNS / "chapter"

MAX_PYQ_IN_PROMPT = 45
TIER_SPEC = {
    "A": {"words": "1800-2500", "label": "deep teaching chapter"},
    "B": {"words": "1000-1500", "label": "standard chapter"},
    "C": {"words": "400-600", "label": "compact fact sheet"},
}

REQUIRED_SECTION_TYPES = {"concept", "crossref", "pyqBank"}
VALID_SECTION_TYPES = {"concept", "table", "mnemonic", "repeats", "pitfalls",
                       "crossref", "pyqBank"}

# reportlab renders characters the built-in fonts lack as solid black boxes, and
# even with DejaVu registered these read badly in print. Normalised on ingest so
# a chapter is never rejected for a typographic detail.
TRANSLITERATE = {
    "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta",
    "κ": "kappa", "λ": "lambda", "μ": "micro", "σ": "sigma",
    "→": "->", "←": "<-", "↑": " increased ", "↓": " decreased ",
    "≥": ">=", "≤": "<=", "≠": "!=", "×": "x", "±": "+/-",
    "–": "-", "—": "-", "‘": "'", "’": "'",
    "“": '"', "”": '"', "…": "...", " ": " ",
    "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4",
    "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁹": "9",
}

TEXTBOOKS = (
    "BD Chaurasia / Snell (Anatomy), Guyton & Ganong (Physiology), "
    "Harper / Lippincott (Biochemistry), Robbins (Pathology), KDT / Katzung "
    "(Pharmacology), Ananthanarayan (Microbiology), Harrison (Medicine), "
    "Bailey & Love / Sabiston (Surgery), Dutta / Shaw (Obs & Gynae), "
    "OP Ghai (Paediatrics), Khurana (Ophthalmology), Dhingra (ENT), "
    "Maheshwari (Orthopaedics), Park (Community Medicine), Reddy (Forensic), "
    "Kaplan & Sadock (Psychiatry), IADVL (Dermatology), Morgan & Mikhail "
    "(Anaesthesia), Sutton / Grainger (Radiology)"
)


def normalise(text: str) -> str:
    for bad, good in TRANSLITERATE.items():
        text = text.replace(bad, good)
    return text


def load_index() -> dict:
    with open(paths.TOPIC_INDEX) as f:
        return json.load(f)


def iter_topics(index: dict):
    for subject, payload in index["subjects"].items():
        for sec in payload["sections"]:
            for t in sec["topics"]:
                yield subject, sec["section"], t


def select_pyqs(topic: dict, by_id: dict) -> list[str]:
    """Pick which questions go into the prompt when a topic has too many.

    Recent NEET PG and INI CET first — they define the current exam. Then one
    representative per repeat cluster, since a repeated concept matters more
    than another near-duplicate of it. Then older questions to fill.
    """
    ids = topic["questionIds"]
    if len(ids) <= MAX_PYQ_IN_PROMPT:
        return ids

    def recent(qid: str) -> bool:
        rec = by_id[qid]
        return rec["exam"] in ("NEET PG", "INI CET") or int(rec["year"]) >= 2019

    picked = [q for q in ids if recent(q)]
    seen = set(picked)
    for cluster in topic.get("repeatClusters", []):
        for qid in cluster:
            if qid not in seen:
                picked.append(qid)
                seen.add(qid)
                break
    for qid in ids:
        if len(picked) >= MAX_PYQ_IN_PROMPT:
            break
        if qid not in seen:
            picked.append(qid)
            seen.add(qid)
    return picked[:MAX_PYQ_IN_PROMPT]


def emit(subject_filter: str | None, tier_filter: str | None) -> None:
    index = load_index()
    by_id = {r["id"]: r for r in dataio.load_master()}
    expl = dataio.load_explanations()

    PACKET_DIR.mkdir(parents=True, exist_ok=True)
    RETURN_DIR.mkdir(parents=True, exist_ok=True)

    # Neighbour names keep chapters from duplicating each other's content.
    neighbours: dict[str, list[str]] = {}
    for subject, payload in index["subjects"].items():
        for sec in payload["sections"]:
            names = [t["topic"] for t in sec["topics"]]
            for t in sec["topics"]:
                neighbours[t["topicId"]] = [n for n in names if n != t["topic"]]

    written = 0
    for subject, section, topic in iter_topics(index):
        if subject_filter and subject != subject_filter:
            continue
        if tier_filter and topic["tier"] != tier_filter:
            continue
        if not topic["questionIds"]:
            continue

        chosen = select_pyqs(topic, by_id)
        spec = TIER_SPEC[topic["tier"]]
        # A topic with more than MAX_PYQ_IN_PROMPT questions ships a selection,
        # so clusters referring to questions left out would ask the writer to
        # cite an id it was never given. Trim them to what is actually in the
        # packet, and report the selected count rather than the topic total.
        chosen_set = set(chosen)
        clusters = [[q for q in c if q in chosen_set] for c in topic.get("repeatClusters", [])]
        clusters = [c for c in clusters if len(c) > 1]
        packet = {
            "topicId": topic["topicId"],
            "topic": topic["topic"],
            "subject": subject,
            "section": section,
            "tier": topic["tier"],
            "highYield": topic["highYield"],
            "targetWords": spec["words"],
            "chapterKind": spec["label"],
            "pyqCount": len(chosen),
            "topicQuestionCount": len(topic["questionIds"]),
            "trend": topic["trend"],
            "byExamYear": topic["byExamYear"],
            "neighbouringTopics": neighbours.get(topic["topicId"], []),
            "repeatClusters": clusters,
            "textbooks": TEXTBOOKS,
            "returnPath": str(
                (RETURN_DIR / f"{topic['topicId']}.json").relative_to(paths.REPO)
            ),
            "pyqs": [
                {
                    "id": qid,
                    "exam": by_id[qid]["exam"],
                    "year": by_id[qid]["year"],
                    "question": by_id[qid]["question"],
                    "options": by_id[qid]["options"],
                    "correctAnswer": by_id[qid]["correctAnswer"],
                    "explanation": (expl.get(qid, {}).get("text")
                                    or by_id[qid].get("explanation") or "")[:900],
                }
                for qid in chosen
            ],
        }
        with open(PACKET_DIR / f"{topic['topicId']}.json", "w") as f:
            json.dump(packet, f, ensure_ascii=False, indent=1)
        written += 1

    print(f"{written} chapter packets -> {PACKET_DIR.relative_to(paths.REPO)}")


def validate(chapter: dict, allowed_ids: set[str]) -> list[str]:
    problems: list[str] = []
    secs = chapter.get("sections")
    if not isinstance(secs, list) or not secs:
        return ["no sections"]

    types = collections.Counter(s.get("type") for s in secs)
    unknown = set(types) - VALID_SECTION_TYPES
    if unknown:
        problems.append(f"unknown section types: {sorted(unknown)}")
    for required in sorted(REQUIRED_SECTION_TYPES):
        if not types.get(required):
            problems.append(f"missing a {required} section")

    if len(chapter.get("mustKnow") or []) < 3:
        problems.append("needs at least 3 mustKnow entries")
    if not (chapter.get("oneLiner") or "").strip():
        problems.append("empty oneLiner")

    cited: set[str] = set()
    for s in secs:
        cited.update(s.get("pyqRefs") or [])
        if s.get("type") == "pyqBank":
            cited.update(s.get("questionIds") or [])
        for item in s.get("items") or []:
            if isinstance(item, dict):
                cited.update(item.get("questionIds") or [])
        if s.get("type") == "table":
            rows = s.get("rows") or []
            cols = s.get("columns") or []
            if not cols or not rows:
                problems.append("table with no columns or no rows")
            elif any(len(r) != len(cols) for r in rows):
                problems.append("table row width does not match its columns")

    # A citation to a question that is not in this topic means the model
    # invented an id, which puts the whole chapter's grounding in doubt.
    invented = sorted(cited - allowed_ids)
    if invented:
        problems.append(f"cites {len(invented)} question ids not in this topic: {invented[:3]}")

    return problems


def _normalise_chapter(node):
    if isinstance(node, str):
        return normalise(node)
    if isinstance(node, list):
        return [_normalise_chapter(x) for x in node]
    if isinstance(node, dict):
        return {k: _normalise_chapter(v) for k, v in node.items()}
    return node


def ingest() -> None:
    index = load_index()
    topic_ids = {t["topicId"]: (subj, sec, t)
                 for subj, sec, t in iter_topics(index)}

    paths.CHAPTERS.mkdir(parents=True, exist_ok=True)
    ok = failed = 0
    problems_by_topic: dict[str, list[str]] = {}

    for ret in sorted(RETURN_DIR.glob("*.json")):
        topic_id = ret.stem
        if topic_id not in topic_ids:
            problems_by_topic[topic_id] = ["unknown topic id"]
            failed += 1
            continue
        subject, section, topic = topic_ids[topic_id]
        try:
            with open(ret) as f:
                chapter = json.load(f)
        except json.JSONDecodeError as e:
            problems_by_topic[topic_id] = [f"invalid JSON: {e}"]
            failed += 1
            continue

        chapter = _normalise_chapter(chapter)
        problems = validate(chapter, set(topic["questionIds"]))
        if problems:
            problems_by_topic[topic_id] = problems
            failed += 1
            continue

        chapter.update({
            "topicId": topic_id, "topic": topic["topic"], "subject": subject,
            "section": section, "tier": topic["tier"],
            "highYield": topic["highYield"], "pyqCount": topic["questionCount"],
        })
        out_dir = paths.CHAPTERS / re.sub(r"[^a-z0-9]+", "-", subject.lower()).strip("-")
        out_dir.mkdir(parents=True, exist_ok=True)
        with open(out_dir / f"{topic_id}.json", "w") as f:
            json.dump(chapter, f, ensure_ascii=False, indent=1)
        ok += 1

    print(f"accepted {ok}, rejected {failed}")
    for topic_id, probs in sorted(problems_by_topic.items())[:25]:
        print(f"  {topic_id}: {'; '.join(probs[:3])}")


def status() -> None:
    packets = list(PACKET_DIR.glob("*.json")) if PACKET_DIR.exists() else []
    returns = {p.stem for p in RETURN_DIR.glob("*.json")} if RETURN_DIR.exists() else set()
    written = list(paths.CHAPTERS.rglob("*.json")) if paths.CHAPTERS.exists() else []
    print(f"packets {len(packets)}, returned {len(returns)}, accepted {len(written)}")
    pending = [p.stem for p in packets if p.stem not in returns]
    if pending:
        print(f"pending {len(pending)}: " + ", ".join(pending[:10]) +
              (" ..." if len(pending) > 10 else ""))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--emit", action="store_true")
    g.add_argument("--ingest", action="store_true")
    g.add_argument("--status", action="store_true")
    ap.add_argument("--subject")
    ap.add_argument("--tier", choices=["A", "B", "C"])
    args = ap.parse_args()
    if args.emit:
        emit(args.subject, args.tier)
    elif args.ingest:
        ingest()
    else:
        status()


if __name__ == "__main__":
    main()
