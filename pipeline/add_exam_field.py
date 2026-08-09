"""Phase 0a — label every question with the exam it came from.

The corpus had no exam field, which made it impossible to tell which questions
actually predict NEET PG. The source the papers were extracted from
(nishantbhushan.in/neetpgquestionpapers) labels them, and the mapping is purely
by year:

    2012-2018  AIPGMEE   — the all-India PG entrance that was renamed NEET PG
    2019-2025  NEET PG   — the exam itself

Nothing is guessed. INI CET questions are labelled by their own ingest script,
not here, because they are not identifiable by year alone (two sessions a year,
and the years overlap with NEET PG).

The 2012-2016 papers are large (1.4k-2.1k questions each) because AIPGMEE ran
as a computer-based test over many sessions and the compilations aggregate
memory-based recalls from all of them. They are one exam, not several merged.

Usage:
    python3 -m pipeline.add_exam_field --dry-run
    python3 -m pipeline.add_exam_field --commit
"""
from __future__ import annotations

import argparse
import collections

from . import dataio, paths

AIPGMEE_YEARS = range(2012, 2019)   # 2012-2018 inclusive
NEETPG_YEARS = range(2019, 2027)    # 2019 onward

AIPGMEE = "AIPGMEE"
NEET_PG = "NEET PG"
INI_CET = "INI CET"

VALID_EXAMS = {AIPGMEE, NEET_PG, INI_CET}


def exam_for_year(year: int) -> str:
    if year in AIPGMEE_YEARS:
        return AIPGMEE
    if year in NEETPG_YEARS:
        return NEET_PG
    raise ValueError(f"no exam mapping for year {year!r}")


def apply(records: list[dict]) -> tuple[list[dict], dict]:
    """Return (updated records, report). Existing `exam` values are respected."""
    stats = collections.Counter()
    for rec in records:
        existing = rec.get("exam")
        if existing:
            if existing not in VALID_EXAMS:
                raise ValueError(f"{rec['id']}: unknown existing exam {existing!r}")
            stats[f"kept:{existing}"] += 1
            continue
        rec["exam"] = exam_for_year(rec["year"])
        stats[f"set:{rec['exam']}"] += 1
    return records, dict(stats)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--commit", action="store_true")
    args = ap.parse_args()
    dry = args.dry_run

    paths.ensure_dirs()
    original = dataio.load_master()
    records = dataio.load_master()   # separate object; save_master diffs the two

    records, stats = apply(records)

    print(f"corpus: {len(records)} questions")
    for k in sorted(stats):
        print(f"  {k}: {stats[k]}")

    by_exam_year = collections.Counter((r["exam"], r["year"]) for r in records)
    print("\nexam x year:")
    for (exam, year) in sorted(by_exam_year, key=lambda t: (t[0], t[1])):
        print(f"  {exam:9s} {year}  {by_exam_year[(exam, year)]:5d}")

    report = dataio.save_master(
        records, changed_fields=["exam"], original=original, dry_run=dry
    )
    print(f"\nmaster: {report}")
    pub = dataio.regen_public(records, dry_run=dry)
    print(f"public: {pub}")
    if dry:
        print("\nDRY RUN — nothing written. Re-run with --commit.")


if __name__ == "__main__":
    main()
