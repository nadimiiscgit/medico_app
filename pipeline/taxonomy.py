"""Phase 1 — build the canonical topic taxonomy.

`topic` is empty on 96% of the corpus, so topic-wise study has nothing behind
it. This builds the two-level structure everything downstream keys off:

    Section   8-12 per subject (~180 total)  — scheduling and PDF chapters
    Topic     18-50 per subject (~500 total) — one study chapter each, and the
                                               tag written onto every question

Topic counts are sized to corpus mass rather than fixed, so Anatomy's 1,342
questions do not get the same granularity as Anaesthesia's 174.

There is no API key available, so the proposal step runs through file-based
work packets: `--emit` writes one packet per subject, a subagent fills in a
return file, and `--ingest` validates and assembles taxonomy.json. Nothing
depends on a long-lived session and any run resumes from disk.

Usage:
    python3 -m pipeline.taxonomy --emit
    python3 -m pipeline.taxonomy --ingest
    python3 -m pipeline.taxonomy --status
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import re

from . import dataio, paths

SAMPLE_SIZE = 200
QUESTIONS_PER_TOPIC = 21
MIN_TOPICS, MAX_TOPICS = 18, 50

# How strongly a paper informs the taxonomy. The taxonomy should describe the
# exam as it is now, not as AIPGMEE was in 2014, so recent papers are sampled
# far more heavily than their share of the corpus would suggest.
EXAM_SAMPLE_WEIGHT = {"NEET PG": 6.0, "INI CET": 6.0, "AIPGMEE": 1.0}
RECENCY_HALFLIFE = 4.0
REF_YEAR = 2026

BANNED_TOPIC_WORDS = {"others", "other", "miscellaneous", "misc", "general",
                      "introduction", "basics", "overview"}

PACKET_DIR = paths.PACKETS / "taxonomy"
RETURN_DIR = paths.RETURNS / "taxonomy"


def slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return re.sub(r"-{2,}", "-", s)


def target_topics(n_questions: int) -> int:
    return max(MIN_TOPICS, min(MAX_TOPICS, round(n_questions / QUESTIONS_PER_TOPIC)))


def sample_weight(rec: dict) -> float:
    exam = EXAM_SAMPLE_WEIGHT.get(rec.get("exam", "AIPGMEE"), 1.0)
    age = max(0, REF_YEAR - int(rec["year"]))
    return exam * (0.5 ** (age / RECENCY_HALFLIFE))


def sample_for(records: list[dict], n: int = SAMPLE_SIZE, seed: int = 42) -> list[dict]:
    """Weighted sample without replacement, so recent papers dominate.

    Every recent question is taken outright when the subject has few of them;
    the remainder is drawn from older papers to keep rare topics represented.
    """
    rng = random.Random(seed)
    recent = [r for r in records if r.get("exam") in ("NEET PG", "INI CET")]
    older = [r for r in records if r.get("exam") not in ("NEET PG", "INI CET")]

    picked = list(recent) if len(recent) <= n else rng.sample(recent, n)
    remaining = n - len(picked)
    if remaining > 0 and older:
        weights = [sample_weight(r) for r in older]
        pool, wts = list(older), list(weights)
        for _ in range(min(remaining, len(pool))):
            i = rng.choices(range(len(pool)), weights=wts, k=1)[0]
            picked.append(pool.pop(i))
            wts.pop(i)
    return picked


def emit() -> None:
    paths.ensure_dirs()
    PACKET_DIR.mkdir(parents=True, exist_ok=True)
    RETURN_DIR.mkdir(parents=True, exist_ok=True)

    records = dataio.load_master()
    by_subject: dict[str, list[dict]] = collections.defaultdict(list)
    for rec in records:
        if rec.get("subject"):
            by_subject[rec["subject"]].append(rec)

    for subject, recs in sorted(by_subject.items()):
        n_topics = target_topics(len(recs))
        n_sections = max(4, min(12, round(n_topics / 4.5)))
        sample = sample_for(recs)
        packet = {
            "subject": subject,
            "questionCount": len(recs),
            "targetTopics": n_topics,
            "targetSections": n_sections,
            "returnPath": str((RETURN_DIR / f"{slug(subject)}.json").relative_to(paths.REPO)),
            "sample": [
                {
                    "id": r["id"],
                    "exam": r.get("exam"),
                    "year": r["year"],
                    "q": r["question"][:320],
                    "opts": " | ".join(f"{k}: {v}" for k, v in r["options"].items())[:220],
                }
                for r in sample
            ],
        }
        out = PACKET_DIR / f"{slug(subject)}.json"
        with open(out, "w") as f:
            json.dump(packet, f, ensure_ascii=False, indent=1)
        print(f"{subject:26s} q={len(recs):5d} topics={n_topics:3d} "
              f"sections={n_sections:2d} sample={len(sample):3d} -> {out.name}")


def validate(subject: str, payload: dict, target: int) -> list[str]:
    """Mechanical checks. Returns a list of problems; empty means it passed."""
    problems: list[str] = []
    sections = payload.get("sections")
    if not isinstance(sections, list) or not sections:
        return ["no sections"]

    topic_names: list[str] = []
    keyword_owner: dict[str, list[str]] = collections.defaultdict(list)

    for sec in sections:
        name = (sec.get("section") or "").strip()
        topics = sec.get("topics") or []
        if not name:
            problems.append("section with no name")
        if len(topics) < 2:
            problems.append(f"section {name!r} has {len(topics)} topic(s), needs >= 2")
        if len(topics) > 12:
            problems.append(f"section {name!r} has {len(topics)} topics, max 12")
        for t in topics:
            tname = (t.get("topic") or "").strip()
            if not tname:
                problems.append(f"unnamed topic in {name!r}")
                continue
            topic_names.append(tname)
            if set(re.findall(r"[a-z]+", tname.lower())) & BANNED_TOPIC_WORDS:
                problems.append(f"topic {tname!r} uses a banned catch-all word")
            for kw in t.get("keywords") or []:
                keyword_owner[kw.strip().lower()].append(tname)

    dupes = [n for n, c in collections.Counter(x.lower() for x in topic_names).items() if c > 1]
    if dupes:
        problems.append(f"duplicate topic names: {dupes[:5]}")

    n = len(topic_names)
    if not (target * 0.85 <= n <= target * 1.15):
        problems.append(f"{n} topics, target {target} (+/-15%)")

    thin = [t for t in topic_names if len(t) < 4]
    if thin:
        problems.append(f"implausibly short topic names: {thin[:5]}")

    return problems


def drop_shared_keywords(payload: dict, max_owners: int = 2) -> int:
    """Remove keywords claimed by too many topics — they cannot discriminate."""
    owner: dict[str, int] = collections.Counter()
    for sec in payload["sections"]:
        for t in sec["topics"]:
            for kw in t.get("keywords") or []:
                owner[kw.strip().lower()] += 1
    dropped = 0
    for sec in payload["sections"]:
        for t in sec["topics"]:
            kept = [k for k in (t.get("keywords") or [])
                    if owner[k.strip().lower()] <= max_owners]
            dropped += len(t.get("keywords") or []) - len(kept)
            t["keywords"] = kept
    return dropped


def ingest() -> None:
    records = dataio.load_master()
    counts = collections.Counter(r["subject"] for r in records if r.get("subject"))

    subjects: dict[str, dict] = {}
    total_topics = 0
    failed: list[str] = []

    for packet_path in sorted(PACKET_DIR.glob("*.json")):
        with open(packet_path) as f:
            packet = json.load(f)
        subject = packet["subject"]
        ret = RETURN_DIR / packet_path.name
        if not ret.exists():
            failed.append(f"{subject}: no return file")
            continue
        with open(ret) as f:
            payload = json.load(f)

        problems = validate(subject, payload, packet["targetTopics"])
        if problems:
            failed.append(f"{subject}: " + "; ".join(problems[:4]))
            continue

        dropped = drop_shared_keywords(payload)
        subject_slug = slug(subject)
        sections = []
        for sec in payload["sections"]:
            topics = []
            for t in sec["topics"]:
                topics.append({
                    "id": f"{subject_slug}.{slug(sec['section'])}.{slug(t['topic'])}",
                    "topic": t["topic"].strip(),
                    "aliases": [a.strip() for a in (t.get("aliases") or []) if a.strip()],
                    "keywords": [k.strip().lower() for k in t.get("keywords") or []],
                })
            sections.append({"section": sec["section"].strip(), "topics": topics})
            total_topics += len(topics)
        subjects[subject] = {"questionCount": counts.get(subject, 0), "sections": sections}
        print(f"  {subject:26s} sections={len(sections):3d} "
              f"topics={sum(len(s['topics']) for s in sections):3d} "
              f"keywords dropped={dropped}")

    if failed:
        print("\nFAILED:")
        for f_ in failed:
            print("  " + f_)

    if not subjects:
        print("\nnothing to write")
        return

    out = {"version": 1, "targetQuestionsPerTopic": QUESTIONS_PER_TOPIC,
           "subjects": subjects}
    paths.TAXONOMY.parent.mkdir(parents=True, exist_ok=True)
    with open(paths.TAXONOMY, "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n{len(subjects)}/{len(list(PACKET_DIR.glob('*.json')))} subjects, "
          f"{total_topics} topics -> {paths.TAXONOMY.relative_to(paths.REPO)}")


def status() -> None:
    packets = sorted(PACKET_DIR.glob("*.json"))
    done = {p.name for p in RETURN_DIR.glob("*.json")}
    missing = [p.stem for p in packets if p.name not in done]
    print(f"packets={len(packets)} returned={len(done)} missing={len(missing)}")
    if missing:
        print("  " + ", ".join(missing))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--emit", action="store_true")
    g.add_argument("--ingest", action="store_true")
    g.add_argument("--status", action="store_true")
    args = ap.parse_args()
    if args.emit:
        emit()
    elif args.ingest:
        ingest()
    else:
        status()


if __name__ == "__main__":
    main()
