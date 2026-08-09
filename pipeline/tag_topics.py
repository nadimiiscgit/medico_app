"""Phase 2 — tag every question with a topic from the taxonomy.

Three stages, cheapest first:

  A  rules   free. Keyword matching against the taxonomy, accepted only when
             the winning topic is clearly ahead of the runner-up.
  B  packets the remainder, batched into work packets a subagent fills in. Each
             packet carries only its own subject's topics, so the classifier
             chooses among 18-50 options rather than 550.
  C  sweep   whatever came back UNSURE or low-confidence, re-run individually.

Results land in a sidecar (data/topics/question_topics.json), never in
questions.json directly — that merge is a separate, guarded step
(pipeline.apply_topics) run only after the sidecar has been inspected.

Usage:
    python3 -m pipeline.tag_topics --rules
    python3 -m pipeline.tag_topics --emit-packets
    python3 -m pipeline.tag_topics --ingest
    python3 -m pipeline.tag_topics --status
"""
from __future__ import annotations

import argparse
import collections
import json
import re

from . import dataio, paths

PACKET_DIR = paths.PACKETS / "tag"
RETURN_DIR = paths.RETURNS / "tag"
PACKET_SIZE = 100

# A rule match is accepted only when the winner is unambiguous: at least this
# many distinct keywords, and this many times the runner-up's score. Anything
# looser mislabels questions silently, which is worse than deferring to stage B.
MIN_HITS = 2
MIN_RATIO = 2.0


def load_taxonomy() -> dict:
    with open(paths.TAXONOMY) as f:
        return json.load(f)


def topics_for_subject(tax: dict, subject: str) -> list[dict]:
    out = []
    for sec in tax["subjects"].get(subject, {}).get("sections", []):
        for t in sec["topics"]:
            out.append({**t, "section": sec["section"]})
    return out


def all_topic_ids(tax: dict) -> dict[str, tuple[str, str, str]]:
    """topic_id -> (subject, section, topic name)"""
    out = {}
    for subject, payload in tax["subjects"].items():
        for sec in payload["sections"]:
            for t in sec["topics"]:
                out[t["id"]] = (subject, sec["section"], t["topic"])
    return out


def _compile(keywords: list[str]) -> list[re.Pattern]:
    pats = []
    for kw in keywords:
        kw = kw.strip()
        if len(kw) < 3:
            continue
        pats.append(re.compile(r"\b" + re.escape(kw).replace(r"\ ", r"\s+") + r"\b", re.I))
    return pats


def build_matchers(tax: dict) -> dict[str, list[tuple[str, list[re.Pattern]]]]:
    matchers: dict[str, list[tuple[str, list[re.Pattern]]]] = {}
    for subject in tax["subjects"]:
        entries = []
        for t in topics_for_subject(tax, subject):
            terms = list(t.get("keywords") or []) + list(t.get("aliases") or [])
            entries.append((t["id"], _compile(terms)))
        matchers[subject] = entries
    return matchers


def searchable(rec: dict, expl: dict) -> str:
    parts = [rec.get("question", "")]
    parts += list(rec.get("options", {}).values())
    text = expl.get(rec["id"], {}).get("text") or rec.get("explanation") or ""
    parts.append(text[:800])
    return " \n ".join(parts)


def rule_match(text: str, entries) -> tuple[str | None, int]:
    scores: list[tuple[int, str]] = []
    for topic_id, pats in entries:
        hits = sum(1 for p in pats if p.search(text))
        if hits:
            scores.append((hits, topic_id))
    if not scores:
        return None, 0
    scores.sort(reverse=True)
    best_hits, best_id = scores[0]
    runner = scores[1][0] if len(scores) > 1 else 0
    if best_hits >= MIN_HITS and best_hits >= max(1, runner) * MIN_RATIO:
        return best_id, best_hits
    return None, best_hits


def load_sidecar() -> dict[str, dict]:
    if paths.QUESTION_TOPICS.exists():
        with open(paths.QUESTION_TOPICS) as f:
            return json.load(f)
    return {}


def save_sidecar(data: dict[str, dict]) -> None:
    paths.QUESTION_TOPICS.parent.mkdir(parents=True, exist_ok=True)
    tmp = paths.QUESTION_TOPICS.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)
    with open(tmp) as f:
        json.load(f)
    tmp.replace(paths.QUESTION_TOPICS)


def run_rules() -> None:
    tax = load_taxonomy()
    lookup = all_topic_ids(tax)
    matchers = build_matchers(tax)
    records = dataio.load_master()
    expl = dataio.load_explanations()

    sidecar = load_sidecar()
    stats = collections.Counter()
    per_subject = collections.Counter()

    for rec in records:
        subject = rec.get("subject")
        entries = matchers.get(subject)
        if not entries:
            stats["no-taxonomy"] += 1
            continue
        if sidecar.get(rec["id"], {}).get("source") == "llm":
            continue                      # never overwrite a classifier result
        topic_id, hits = rule_match(searchable(rec, expl), entries)
        if topic_id:
            s, sec, name = lookup[topic_id]
            sidecar[rec["id"]] = {
                "subject": s, "section": sec, "topic": name,
                "topicId": topic_id, "confidence": "rule", "source": "rule",
                "hits": hits,
            }
            stats["matched"] += 1
            per_subject[subject] += 1
        else:
            stats["deferred"] += 1

    save_sidecar(sidecar)
    total = sum(1 for r in records if r.get("subject") in matchers)
    print(f"rule pass: matched {stats['matched']}/{total} "
          f"({stats['matched'] / max(1, total) * 100:.1f}%), "
          f"deferred {stats['deferred']}, no-taxonomy {stats['no-taxonomy']}")
    print("\nper subject:")
    counts = collections.Counter(r["subject"] for r in records)
    for subject in sorted(matchers):
        n = counts.get(subject, 0)
        m = per_subject.get(subject, 0)
        print(f"  {subject:26s} {m:5d}/{n:5d}  {m / max(1, n) * 100:5.1f}%")


def emit_packets(sweep: bool = False) -> None:
    """Write packets for everything still untagged.

    `sweep` is the second pass over what the first one returned UNSURE or
    could not place. It uses smaller batches and hands over the full
    explanation and the section each topic sits under, because the questions
    that survive the first pass are the genuinely ambiguous ones and need the
    extra context to be placed at all.
    """
    tax = load_taxonomy()
    records = dataio.load_master()
    expl = dataio.load_explanations()
    sidecar = load_sidecar()
    prefix = "sweep-" if sweep else ""
    size = 40 if sweep else PACKET_SIZE

    PACKET_DIR.mkdir(parents=True, exist_ok=True)
    RETURN_DIR.mkdir(parents=True, exist_ok=True)

    # Emit is incremental: a subject that already has packets is left alone.
    # Packet numbering runs over the currently-untagged set, so re-emitting a
    # subject would rewrite the same filenames with different questions and
    # corrupt any work in flight against them.
    # Only the current pass's own packets count: a first-pass packet must not
    # make the sweep think that subject is done, and vice versa.
    have_packets = set()
    for existing in PACKET_DIR.glob("*.json"):
        is_sweep = existing.name.startswith("sweep-")
        if is_sweep == sweep:
            have_packets.add(existing.name.rsplit("-", 1)[0])

    todo: dict[str, list[dict]] = collections.defaultdict(list)
    for rec in records:
        subject = rec.get("subject")
        if subject not in tax["subjects"]:
            continue
        if rec["id"] in sidecar:
            continue
        todo[subject].append(rec)

    written = skipped_subjects = 0
    for subject, recs in sorted(todo.items()):
        slug = re.sub(r"[^a-z0-9]+", "-", subject.lower()).strip("-")
        if f"{prefix}{slug}" in have_packets:
            skipped_subjects += 1
            continue
        topics = [
            {"id": t["id"], "section": t["section"], "topic": t["topic"]}
            for t in topics_for_subject(tax, subject)
        ]
        chunks = [recs[i:i + size] for i in range(0, len(recs), size)]
        for n, chunk in enumerate(chunks, start=1):
            name = f"{prefix}{slug}-{n:02d}.json"
            packet = {
                "subject": subject,
                "topics": topics,
                "returnPath": str((RETURN_DIR / name).relative_to(paths.REPO)),
                "questions": [
                    {
                        "id": r["id"],
                        "q": r["question"][:400],
                        "opts": " | ".join(f"{k}: {v}" for k, v in r["options"].items())[:260],
                        "expl": (expl.get(r["id"], {}).get("text")
                                 or r.get("explanation") or "")[:1400 if sweep else 600],
                    }
                    for r in chunk
                ],
            }
            with open(PACKET_DIR / name, "w") as f:
                json.dump(packet, f, ensure_ascii=False, indent=1)
            written += 1

    remaining = sum(len(v) for v in todo.values())
    print(f"{remaining} untagged questions -> {written} new packets in "
          f"{PACKET_DIR.relative_to(paths.REPO)}"
          + (f" ({skipped_subjects} subject(s) already had packets)" if skipped_subjects else ""))
    for subject, recs in sorted(todo.items(), key=lambda kv: -len(kv[1])):
        print(f"  {subject:26s} {len(recs):5d}")


def ingest() -> None:
    tax = load_taxonomy()
    lookup = all_topic_ids(tax)
    records = {r["id"]: r for r in dataio.load_master()}
    sidecar = load_sidecar()

    added = rejected = unsure = 0
    problems = collections.Counter()

    for ret in sorted(RETURN_DIR.glob("*.json")):
        with open(ret) as f:
            payload = json.load(f)
        rows = payload if isinstance(payload, list) else payload.get("assignments", [])
        for row in rows:
            qid = row.get("id")
            topic_id = row.get("topicId") or row.get("topic_id")
            if qid not in records:
                problems["unknown-question-id"] += 1
                continue
            if not topic_id or topic_id == "UNSURE":
                unsure += 1
                continue
            if topic_id not in lookup:
                problems["topic-id-not-in-taxonomy"] += 1
                rejected += 1
                continue
            subject, section, name = lookup[topic_id]
            # A topic from another subject is a hallucination, not a judgement call.
            if subject != records[qid].get("subject"):
                problems["cross-subject-topic"] += 1
                rejected += 1
                continue
            sidecar[qid] = {
                "subject": subject, "section": section, "topic": name,
                "topicId": topic_id,
                "confidence": row.get("confidence", "medium"), "source": "llm",
            }
            added += 1

    save_sidecar(sidecar)
    print(f"ingested {added}, rejected {rejected}, unsure {unsure}")
    for k, v in problems.most_common():
        print(f"  {k}: {v}")
    status()


def status() -> None:
    records = dataio.load_master()
    sidecar = load_sidecar()
    tagged = sum(1 for r in records if r["id"] in sidecar)
    print(f"\ntagged {tagged}/{len(records)} ({tagged / len(records) * 100:.1f}%)")
    src = collections.Counter(v.get("source") for v in sidecar.values())
    print("  by source:", dict(src))
    missing = collections.Counter(
        r["subject"] for r in records if r["id"] not in sidecar
    )
    if missing:
        print("  untagged by subject:")
        for s, n in missing.most_common():
            print(f"    {s:26s} {n}")
    if PACKET_DIR.exists():
        packets = list(PACKET_DIR.glob("*.json"))
        done = {p.name for p in RETURN_DIR.glob("*.json")} if RETURN_DIR.exists() else set()
        pending = [p.stem for p in packets if p.name not in done]
        print(f"  packets {len(packets)}, returned {len(packets) - len(pending)}, "
              f"pending {len(pending)}")
        if pending:
            print("    " + ", ".join(pending[:20]) + (" ..." if len(pending) > 20 else ""))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--rules", action="store_true")
    g.add_argument("--emit-packets", action="store_true")
    g.add_argument("--sweep", action="store_true",
                   help="second pass over whatever the first pass left untagged")
    g.add_argument("--ingest", action="store_true")
    g.add_argument("--status", action="store_true")
    args = ap.parse_args()
    if args.rules:
        run_rules()
    elif args.emit_packets or args.sweep:
        emit_packets(sweep=args.sweep)
    elif args.ingest:
        ingest()
    else:
        status()


if __name__ == "__main__":
    main()
