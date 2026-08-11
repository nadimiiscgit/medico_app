"""Empty the 'General Medicine' bucket before the taxonomy is built.

'General Medicine' was never a real subject in this corpus — it is the fallback
the original subject classifier used when it could not decide, and 27 questions
were left sitting in it. Left alone it would get its own 18-topic taxonomy and
its own chapters, splitting immunology away from Microbiology for no reason.

The 27 are small enough to assign by hand, which is more reliable than another
classifier pass. The bulk are immunology (complement, HLA, immunoglobulins,
interleukins), which this corpus files under Microbiology.

Usage:
    python3 -m pipeline.fix_general_medicine --dry-run
    python3 -m pipeline.fix_general_medicine --commit
"""
from __future__ import annotations

import argparse
import collections

from . import dataio

# question id -> subject, with the reason it is not Microbiology where relevant
REASSIGN = {
    # Immunology: complement, immunoglobulins, HLA, interleukins
    "neetpg-2012-s1-q0751": "Microbiology",
    "neetpg-2012-s1-q0753": "Microbiology",
    "neetpg-2012-s1-q0754": "Microbiology",
    "neetpg-2012-s1-q0755": "Microbiology",
    "neetpg-2012-s1-q0756": "Microbiology",
    "neetpg-2012-s1-q0758": "Microbiology",
    "neetpg-2012-s1-q0759": "Microbiology",
    "neetpg-2014-s1-q0880": "Microbiology",
    "neetpg-2014-s1-q0881": "Microbiology",
    "neetpg-2014-s1-q0882": "Microbiology",
    "neetpg-2014-s1-q0883": "Microbiology",
    "neetpg-2014-s1-q0884": "Microbiology",
    "neetpg-2014-s1-q0887": "Microbiology",
    "neetpg-2015-s1-q0405": "Microbiology",
    "neetpg-2015-s1-q0407": "Microbiology",
    "neetpg-2015-s1-q0411": "Microbiology",
    "neetpg-2015-s1-q0416": "Microbiology",
    "neetpg-2017-s1-q0042": "Microbiology",
    "neetpg-2018-s1-q0036": "Microbiology",
    "neetpg-2020-s1-q0090": "Microbiology",
    # Vestibular testing and nystagmus characterisation are taught in ENT
    "neetpg-2013-s1-q0999": "ENT",
    "neetpg-2024-s1-q0042": "ENT",
    # Down-beat nystagmus localises to the craniocervical junction / brainstem
    "neetpg-2013-s1-q1201": "Medicine",
    "neetpg-2013-s1-q1202": "Medicine",
    # Congenital adrenal hypoplasia and its intersex phenotype — endocrinology
    "neetpg-2018-s1-q0289": "Medicine",
    # Particle therapy selection for chordoma
    "neetpg-2018-s1-q0276": "Radiology",
    # Ocular motility loss localised to a cranial nerve palsy
    "neetpg-2020-s1-q0271": "Ophthalmology",
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--commit", action="store_true")
    args = ap.parse_args()
    dry = args.dry_run

    original = dataio.load_master()
    records = dataio.load_master()

    stranded = [r["id"] for r in records if r["subject"] == "General Medicine"]
    unmapped = sorted(set(stranded) - set(REASSIGN))
    if unmapped:
        raise SystemExit(f"{len(unmapped)} General Medicine questions have no mapping: {unmapped}")

    moved = collections.Counter()
    for rec in records:
        target = REASSIGN.get(rec["id"])
        if target and rec["subject"] == "General Medicine":
            rec["subject"] = target
            moved[target] += 1

    print(f"reassigned {sum(moved.values())} questions out of General Medicine:")
    for subject, n in moved.most_common():
        print(f"  {subject:16s} {n}")
    remaining = sum(1 for r in records if r["subject"] == "General Medicine")
    print(f"remaining in General Medicine: {remaining}")

    print(dataio.save_master(records, changed_fields=["subject"],
                             original=original, dry_run=dry))
    print(dataio.regen_public(records, dry_run=dry))
    if dry:
        print("\nDRY RUN — nothing written. Re-run with --commit.")


if __name__ == "__main__":
    main()
