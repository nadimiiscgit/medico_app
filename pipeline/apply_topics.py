"""Phase 2d — merge the topic sidecar into the corpus.

Kept separate from tagging on purpose: tagging writes only to
data/topics/question_topics.json, so a bad classifier run can never touch the
corpus. This step is run once, after the sidecar has been inspected, and it
declares exactly which fields it is allowed to change so dataio.save_master can
reject anything else.

`tags` is populated here too. It has been an empty list on every record since
the corpus was built; filling it with [exam, section, topic] makes exam and
topic filterable in the app without any schema change.

Usage:
    python3 -m pipeline.apply_topics --dry-run
    python3 -m pipeline.apply_topics --commit
"""
from __future__ import annotations

import argparse
import collections
import json

from . import dataio, paths

# `subject` is included because the sweep may move a question to a different
# subject: the original extraction inherited the papers' section headings, and
# those file Ophthalmology, ENT and Orthopaedics under "Surgery".
CHANGED_FIELDS = ["subject", "topic", "section", "topicId", "tags"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--commit", action="store_true")
    ap.add_argument("--min-confidence", default="low",
                    choices=["low", "medium", "high", "rule"],
                    help="skip assignments below this confidence")
    args = ap.parse_args()
    dry = args.dry_run

    order = {"low": 0, "medium": 1, "rule": 2, "high": 2}
    floor = order[args.min_confidence]

    with open(paths.QUESTION_TOPICS) as f:
        sidecar = json.load(f)

    original = dataio.load_master()
    records = dataio.load_master()

    applied = skipped = moved = 0
    for rec in records:
        tag = sidecar.get(rec["id"])
        if not tag or order.get(tag.get("confidence", "medium"), 1) < floor:
            skipped += 1
            continue
        if tag.get("movedFrom"):
            rec["subject"] = tag["subject"]
            moved += 1
        rec["topic"] = tag["topic"]
        rec["section"] = tag["section"]
        rec["topicId"] = tag["topicId"]
        rec["tags"] = [rec["exam"], tag["section"], tag["topic"]]
        applied += 1

    print(f"applied {applied}, skipped {skipped}, moved subject {moved}, total {len(records)}")
    untagged = collections.Counter(
        r["subject"] for r in records if not r.get("topicId")
    )
    if untagged:
        print("still untagged:")
        for s, n in untagged.most_common():
            print(f"  {s:26s} {n}")
    else:
        print("every question carries a topic")

    print(dataio.save_master(records, changed_fields=CHANGED_FIELDS,
                             original=original, dry_run=dry))
    print(dataio.regen_public(records, dry_run=dry))
    if dry:
        print("\nDRY RUN — nothing written. Re-run with --commit.")


if __name__ == "__main__":
    main()
