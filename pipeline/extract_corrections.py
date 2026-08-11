"""Collect the answer-key disagreements the chapters flagged.

The chapter prompt forbids silently resolving a conflict between the writer's
knowledge and a supplied explanation: it must state the correct fact *and* log
a `pitfalls` entry naming the question. Those entries turn out to be one of the
most valuable things the pipeline produces, because the corpus contains real
errors — 41% of its explanations are machine-written, and every paper from 2025
on is a memory-based student recall whose key was reconstructed from memory.

Studying a wrong key is worse than not studying the question at all, so they
are collected here into one document to read before the exam.

Usage:
    python3 -m pipeline.extract_corrections
"""
from __future__ import annotations

import argparse
import json
import re

from . import dataio, paths

# A pitfall counts as a key disagreement when it names a question and talks
# about the key or explanation being wrong.
QUESTION_ID = re.compile(r"\b((?:neetpg|inicet)-\d{4}-[a-z0-9]+-q\d+)\b")
DISAGREEMENT = re.compile(
    r"\b(key|keyed|keys|answer|incorrect|wrong|contradict\w*|disagree\w*|"
    r"explanation|concedes|misstate\w*)\b", re.I)

OUT = paths.DOCS / "ANSWER-KEY-CORRECTIONS.md"


def collect() -> list[dict]:
    found: list[dict] = []
    if not paths.CHAPTERS.exists():
        return found
    for path in sorted(paths.CHAPTERS.rglob("*.json")):
        with open(path) as f:
            chapter = json.load(f)
        for section in chapter.get("sections", []):
            if section.get("type") != "pitfalls":
                continue
            for item in section.get("items") or []:
                ids = QUESTION_ID.findall(item)
                if ids and DISAGREEMENT.search(item):
                    found.append({
                        "subject": chapter["subject"],
                        "topic": chapter["topic"],
                        "topicId": chapter["topicId"],
                        "questionIds": ids,
                        "note": item.strip(),
                    })
    return found


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()

    entries = collect()
    by_id = {r["id"]: r for r in dataio.load_master()}

    lines = [
        "# Answer keys worth double-checking",
        "",
        "Every entry here is a place where the study material disagrees with the",
        "answer key or the explanation stored against a previous-year question.",
        "",
        "This list exists because the corpus is not authoritative. Roughly 41% of its",
        "explanations are machine-written, and every paper from 2025 onward is a",
        "memory-based recall reconstructed by students — so its keys are evidence,",
        "not fact. Learning a wrong key confidently is worse than skipping the",
        "question, which is why each disagreement is written down rather than",
        "silently resolved.",
        "",
        "**These are claims to verify, not corrections to trust.** Check anything here",
        "against your own textbook before you rely on it — particularly doses,",
        "numerical cut-offs and national programme figures.",
        "",
        f"**{len(entries)} disagreements flagged so far.** The list grows as more",
        "chapters are written; regenerate with `python3 -m pipeline.extract_corrections`.",
        "",
    ]

    by_subject: dict[str, list[dict]] = {}
    for e in entries:
        by_subject.setdefault(e["subject"], []).append(e)

    for subject in sorted(by_subject):
        lines += [f"## {subject}", ""]
        current_topic = None
        for e in by_subject[subject]:
            if e["topic"] != current_topic:
                current_topic = e["topic"]
                lines += [f"### {current_topic}", ""]
            for qid in e["questionIds"]:
                rec = by_id.get(qid)
                if rec:
                    correct = rec["options"].get(rec["correctAnswer"], "")
                    lines.append(
                        f"- **`{qid}`** ({rec['exam']} {rec['year']}) — "
                        f"*{rec['question'][:150]}*  \n"
                        f"  Stored key: **{rec['correctAnswer']}. {correct[:90]}**"
                    )
                else:
                    lines.append(f"- **`{qid}`**")
            lines += [f"  \n  {e['note']}", ""]

    paths.DOCS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines))
    print(f"{len(entries)} disagreements across {len(by_subject)} subjects "
          f"-> {OUT.relative_to(paths.REPO)}")
    for subject in sorted(by_subject, key=lambda s: -len(by_subject[s])):
        print(f"  {subject:26s} {len(by_subject[subject])}")


if __name__ == "__main__":
    main()
