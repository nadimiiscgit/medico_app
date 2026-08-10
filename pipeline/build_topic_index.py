"""Phase 3 — rank topics by what the exam actually keeps asking.

The naive ranking is a raw question count, and it is badly wrong here: AIPGMEE
2014 alone contributed 2,104 questions while NEET PG 2024 contributed 110, so
counting would let one 2014 compilation outvote the last three real papers.

Instead each topic is scored on its **share of its own paper**, weighted by how
much that paper predicts the 2026 NEET PG:

    w(paper) = exam_weight * exp(-(2026 - year) / 4)

    NEET PG 2025   0.78      INI CET May 2026  0.60
    NEET PG 2024   0.61      INI CET 2025      0.47
    NEET PG 2020   0.22      AIPGMEE 2014      0.02

So recent NEET PG and INI CET papers decide the ranking, while the 9,277
AIPGMEE questions act as a weak prior that orders topics the recent papers
happen not to have touched — without ever outvoting them.

The shrinkage term keeps a 2-of-200 fluke in a single paper from scoring as
"2 expected questions". The result is expressed as expected questions in a
200-question paper, so the numbers sum to ~200 and mean something.

Usage:
    python3 -m pipeline.build_topic_index
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import re

from . import dataio, pace, paths

REF_YEAR = 2026
RECENCY_TAU = 4.0
SHRINKAGE = 25.0
PAPER_LENGTH = 200

EXAM_WEIGHT = {"NEET PG": 1.0, "INI CET": 0.6, "AIPGMEE": 0.45}

# Tiers are percentile bands, not absolute cut-offs. With ~570 topics sharing
# 200 expected questions the average topic is worth ~0.35, so a fixed ">= 1.0
# is tier A" rule leaves only a couple of dozen topics in the band that gets the
# deepest chapters and drives the revision PDF. The bands below allocate chapter
# depth and study order; `highYield` remains the literal expected-question count.
TIER_A_PERCENTILE = 0.20
TIER_B_PERCENTILE = 0.55

# The PG Masters table is a second recall of NEET PG 2025, which is already
# represented by its full-MCQ recall. Counting both would double-weight the
# single most heavily weighted paper in the corpus.
EXCLUDE_ID_PREFIXES = ("neetpg-2025-recall",)

STOPWORDS = {
    "the", "of", "in", "is", "a", "an", "and", "or", "to", "for", "with", "on",
    "at", "by", "from", "which", "what", "following", "all", "not", "true",
    "false", "except", "most", "common", "commonly", "seen", "are", "was",
    "this", "that", "it", "as", "be", "has", "have", "his", "her", "patient",
    "years", "year", "old", "case", "about", "into", "due", "can", "may",
}


def paper_weight(exam: str, year: int) -> float:
    base = EXAM_WEIGHT.get(exam, 0.45)
    return base * math.exp(-(REF_YEAR - int(year)) / RECENCY_TAU)


def tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z]{3,}", text.lower())
    return {w for w in words if w not in STOPWORDS}


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if len(a) > len(b):
        a, b = b, a
    dot = sum(v * b.get(k, 0.0) for k, v in a.items())
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def repeat_clusters(records: list[dict], threshold: float = 0.82) -> list[list[str]]:
    """Group near-duplicate questions within a topic.

    A concept asked in several different papers is the strongest signal that it
    will be asked again, so these drive both the score and the chapter's
    'asked again and again' section.
    """
    if len(records) < 2:
        return []
    docs = []
    for r in records:
        correct = r.get("options", {}).get(r.get("correctAnswer", ""), "")
        docs.append((r["id"], tokens(f"{r.get('question','')} {correct}")))

    df: collections.Counter = collections.Counter()
    for _, toks in docs:
        df.update(toks)
    n = len(docs)
    vecs = []
    for qid, toks in docs:
        vecs.append((qid, {t: math.log(n / (1 + df[t])) + 1.0 for t in toks}))

    parent = {qid: qid for qid, _ in vecs}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(len(vecs)):
        for j in range(i + 1, len(vecs)):
            if cosine(vecs[i][1], vecs[j][1]) >= threshold:
                a, b = find(vecs[i][0]), find(vecs[j][0])
                if a != b:
                    parent[a] = b

    groups: dict[str, list[str]] = collections.defaultdict(list)
    for qid, _ in vecs:
        groups[find(qid)].append(qid)
    return sorted((g for g in groups.values() if len(g) > 1), key=len, reverse=True)


def trend(by_paper: dict[tuple[str, int], int]) -> str:
    recent = sum(c for (exam, year), c in by_paper.items() if year >= 2019)
    older = sum(c for (exam, year), c in by_paper.items() if year < 2019)
    if recent == 0 and older == 0:
        return "unasked"
    if recent >= max(1, older) * 0.6:
        return "rising"
    if recent == 0:
        return "falling"
    return "stable"


def build(pace_cfg: pace.Pace = pace.DEFAULT, scope: str = "recent") -> dict:
    with open(paths.TAXONOMY) as f:
        tax = json.load(f)
    with open(paths.QUESTION_TOPICS) as f:
        sidecar = json.load(f)

    records = [
        r for r in dataio.load_master()
        if not r["id"].startswith(EXCLUDE_ID_PREFIXES)
    ]
    by_id = {r["id"]: r for r in records}

    # Paper sizes and weights, counting only questions that carry a topic.
    paper_total: collections.Counter = collections.Counter()
    topic_paper: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    topic_ids: dict[str, list[str]] = collections.defaultdict(list)

    for qid, tag in sidecar.items():
        rec = by_id.get(qid)
        if not rec:
            continue
        paper = (rec["exam"], int(rec["year"]))
        paper_total[paper] += 1
        topic_paper[tag["topicId"]][paper] += 1
        topic_ids[tag["topicId"]].append(qid)

    total_tagged = sum(paper_total.values())
    weights = {p: paper_weight(*p) for p in paper_total}
    weight_sum = sum(weights.values()) or 1.0

    def high_yield(topic_id: str) -> float:
        counts = topic_paper[topic_id]
        prior = len(topic_ids[topic_id]) / max(1, total_tagged)
        acc = 0.0
        for paper, n_paper in paper_total.items():
            share = (counts.get(paper, 0) + SHRINKAGE * prior) / (n_paper + SHRINKAGE)
            acc += weights[paper] * share
        return PAPER_LENGTH * acc / weight_sum

    # Tier boundaries are set once, across every subject, so a tier means the
    # same thing everywhere rather than being relative to its own subject.
    all_scores = sorted(
        (high_yield(t["id"])
         for payload in tax["subjects"].values()
         for sec in payload["sections"] for t in sec["topics"]),
        reverse=True,
    )
    def _at(fraction: float) -> float:
        if not all_scores:
            return 0.0
        return all_scores[min(len(all_scores) - 1, int(len(all_scores) * fraction))]

    cut_a, cut_b = _at(TIER_A_PERCENTILE), _at(TIER_B_PERCENTILE)

    def tier_of(score: float) -> str:
        return "A" if score >= cut_a else ("B" if score >= cut_b else "C")

    subjects: dict[str, dict] = {}
    for subject, payload in tax["subjects"].items():
        sections = []
        for sec in payload["sections"]:
            topics = []
            for t in sec["topics"]:
                ids = topic_ids.get(t["id"], [])
                hy = round(high_yield(t["id"]), 3)
                counts = topic_paper[t["id"]]
                topics.append({
                    "topicId": t["id"],
                    "topic": t["topic"],
                    "section": sec["section"],
                    "subject": subject,
                    "questionCount": len(ids),
                    "byExamYear": {f"{e} {y}": c for (e, y), c in sorted(counts.items())},
                    "byYear": _by_year(counts),
                    "questionIds": sorted(ids),
                    "highYield": hy,
                    "tier": tier_of(hy),
                    "trend": trend(counts),
                    "repeatClusters": repeat_clusters([by_id[i] for i in ids]),
                })
                # Estimated from the chapter's real size and the questions actually
                # scheduled, not from the yield score — see pipeline/pace.py.
                est = pace.estimate(topics[-1], subject, by_id,
                                    pace=pace_cfg, scope=scope)
                topics[-1].update({
                    "estMinutes": est["minutes"],
                    "estReadMinutes": est["readMinutes"],
                    "estSolveMinutes": est["solveMinutes"],
                    "selectedPyqCount": len(est["selectedPyqIds"]),
                    "selectedPyqIds": est["selectedPyqIds"],
                    "chapterMeasured": est["measured"],
                })
            sections.append({
                "section": sec["section"],
                "questionCount": sum(t["questionCount"] for t in topics),
                "highYield": round(sum(t["highYield"] for t in topics), 3),
                "topics": sorted(topics, key=lambda t: -t["highYield"]),
            })
        subjects[subject] = {
            "questionCount": sum(s["questionCount"] for s in sections),
            "highYield": round(sum(s["highYield"] for s in sections), 3),
            "sections": sorted(sections, key=lambda s: -s["highYield"]),
        }

    return {
        "paperLength": PAPER_LENGTH,
        "referenceYear": REF_YEAR,
        "examWeights": EXAM_WEIGHT,
        "recencyHalfLifeYears": round(RECENCY_TAU * math.log(2), 2),
        "tierCutoffs": {"A": round(cut_a, 3), "B": round(cut_b, 3)},
        "papers": [
            {"exam": e, "year": y, "questions": n, "weight": round(weights[(e, y)], 3)}
            for (e, y), n in sorted(paper_total.items())
        ],
        "totalTagged": total_tagged,
        "subjects": subjects,
    }


def _by_year(counts: collections.Counter) -> dict[str, int]:
    out: collections.Counter = collections.Counter()
    for (_exam, year), c in counts.items():
        out[str(year)] += c
    return dict(sorted(out.items()))


def slim(index: dict) -> dict:
    """App-sized copy: drops question ids and clusters, which dominate the size."""
    out = json.loads(json.dumps(index))
    for subject in out["subjects"].values():
        for sec in subject["sections"]:
            for t in sec["topics"]:
                t.pop("questionIds", None)
                t.pop("repeatClusters", None)
                t.pop("selectedPyqIds", None)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    pace.add_pace_args(ap)
    ap.add_argument("--pyq-scope", choices=pace.SCOPES, default="recent",
                    help="which questions the plan schedules (default: recent)")
    args = ap.parse_args()

    index = build(pace.pace_from_args(args), args.pyq_scope)
    index["pace"] = {
        "wpm": args.wpm, "pyqMinutes": args.pyq_minutes,
        "rowSeconds": args.row_seconds, "mkSeconds": args.mk_seconds,
        "pyqScope": args.pyq_scope,
    }
    paths.TOPIC_INDEX.parent.mkdir(parents=True, exist_ok=True)
    with open(paths.TOPIC_INDEX, "w") as f:
        json.dump(index, f, ensure_ascii=False, indent=1)
    with open(paths.TOPIC_INDEX_SLIM, "w") as f:
        json.dump(slim(index), f, ensure_ascii=False, separators=(",", ":"))

    flat = [t for s in index["subjects"].values()
            for sec in s["sections"] for t in sec["topics"]]
    tiers = collections.Counter(t["tier"] for t in flat)
    total_hy = sum(t["highYield"] for t in flat)
    clustered = sum(len(t["repeatClusters"]) for t in flat)

    print(f"papers: {len(index['papers'])}, tagged questions: {index['totalTagged']}")
    print(f"topics: {len(flat)}  tiers: A={tiers['A']} B={tiers['B']} C={tiers['C']}")
    print(f"sum of expected questions: {total_hy:.1f} (should be near {PAPER_LENGTH})")
    print(f"repeat clusters found: {clustered}")

    read = sum(t["estReadMinutes"] for t in flat)
    solve = sum(t["estSolveMinutes"] for t in flat)
    scheduled = sum(t["selectedPyqCount"] for t in flat)
    measured = sum(1 for t in flat if t.get("chapterMeasured"))
    print(f"\nestimated study load at {args.wpm:g} wpm, {args.pyq_minutes:g} min/MCQ:")
    print(f"  reading {read/60:6.1f} h")
    print(f"  solving {solve/60:6.1f} h  ({scheduled} of "
          f"{sum(t['questionCount'] for t in flat)} questions, scope={args.pyq_scope})")
    print(f"  TOTAL   {(read+solve)/60:6.1f} h")
    print(f"  ({measured} of {len(flat)} topics estimated from a real chapter, "
          f"the rest from tier defaults)")

    print("\nsubjects by expected questions:")
    for subject, payload in sorted(index["subjects"].items(),
                                   key=lambda kv: -kv[1]["highYield"]):
        print(f"  {subject:26s} {payload['highYield']:6.1f}  ({payload['questionCount']} q)")

    print("\ntop 25 topics:")
    for t in sorted(flat, key=lambda t: -t["highYield"])[:25]:
        print(f"  {t['highYield']:5.2f} [{t['tier']}] {t['subject'][:14]:14s} "
              f"{t['topic'][:44]:44s} n={t['questionCount']:4d} {t['trend']}")


if __name__ == "__main__":
    main()
