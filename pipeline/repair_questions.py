"""Repair individual questions where the missing evidence was actually recoverable.

Two of the fourteen questions the adjudication marked broken turned out to be
fixable from evidence elsewhere in the corpus, rather than needing the paper
rewritten. Both repairs are recorded here as explicit literals, with the evidence
that justifies them, because a hand-checked pair is more trustworthy than another
classifier pass over two items.

Usage:
    python3 -m pipeline.repair_questions --dry-run
    python3 -m pipeline.repair_questions --commit
"""
from __future__ import annotations

import argparse

from . import dataio

REPAIRS = [
    {
        "id": "neetpg-2025-s1-q0132",
        "question": (
            "Which of the following conditions is most likely to follow this pattern "
            "of inheritance? [Pedigree, reconstructed from an independent recall of "
            "the same paper: the affected mother transmits the disease to all of her "
            "children, while affected fathers transmit it to none.]"
        ),
        "correctAnswer": "C",
        "explanation": (
            "A pedigree in which every child of an affected mother is affected, and no "
            "child of an affected father is, describes MITOCHONDRIAL (maternal) "
            "inheritance. Mitochondria are inherited almost exclusively from the oocyte, "
            "so transmission runs only down the female line, and both sons and daughters "
            "are affected - which distinguishes it from X-linked recessive inheritance, "
            "where affected mothers are usually carriers and only sons are affected.\n\n"
            "Of the four options only Kearns-Sayre syndrome is mitochondrial. It is caused "
            "by a large-scale deletion of mitochondrial DNA and presents with the triad of "
            "progressive external ophthalmoplegia, pigmentary retinopathy and onset before "
            "20 years, often with heart block. Note the nuance: single large-scale deletions "
            "are usually sporadic rather than inherited, so a pedigree showing clean maternal "
            "transmission fits mitochondrial point mutations better - but Kearns-Sayre remains "
            "the only mitochondrial disorder offered.\n\n"
            "Marfan syndrome (the stored key) is autosomal dominant: an affected father "
            "transmits it to half his children, which the pedigree explicitly excludes. "
            "Prader-Willi involves imprinting with paternal deletion, and Duchenne is "
            "X-linked recessive.\n\n"
            "Answer corrected from B to C. The pedigree image was lost from this "
            "memory-based recall; its content was recovered from a second, independent "
            "recall of the same paper (PG Masters), which records the pedigree as 'mother "
            "giving disease to all children, but father to none' and answers Kearns-Sayre."
        ),
        "why": "pedigree recovered from an independent recall of the same paper",
    },
    {
        "id": "neetpg-2022-s1-q0123",
        "correctAnswer": "D",
        "explanation": (
            "The stem states the histopathology showed DICHOTOMOUS BRANCHING, and that "
            "settles it. Aspergillus has septate hyphae branching dichotomously at acute, "
            "roughly 45-degree angles. The Mucorales - Rhizopus, Mucor, Absidia - have "
            "broad, ribbon-like, aseptate (coenocytic) hyphae branching irregularly at wide, "
            "roughly 90-degree angles, and are never described as dichotomous.\n\n"
            "A second argument points the same way. The paper offers Rhizopus and Mucor as "
            "two SEPARATE options. Both are Mucorales, so if the intended answer were "
            "mucormycosis the question would have two correct options and no single defensible "
            "key. An examiner offering both cannot have intended either.\n\n"
            "The diabetic context is a genuine distractor: diabetes predisposes to both. "
            "Mucormycosis in diabetes is classically RHINO-ORBITO-CEREBRAL and tied to "
            "ketoacidosis, whereas this patient has pneumonia, which is the usual form of "
            "invasive aspergillosis. Learn the pairing by hyphal morphology first and the "
            "clinical setting second.\n\n"
            "Answer corrected from B to D. The accompanying image has been restored to the "
            "corpus but is too low in resolution to demonstrate septation independently, so "
            "this correction rests on the stem's own wording and the split-option argument, "
            "not on the picture."
        ),
        "why": "stem says dichotomous branching; Mucorales are aseptate and wide-angle",
    },
]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--commit", action="store_true")
    args = ap.parse_args()
    dry = args.dry_run

    original = dataio.load_master()
    records = dataio.load_master()
    by_id = {r["id"]: r for r in records}
    expl = dataio.load_explanations()

    changed_fields: set[str] = set()
    for spec in REPAIRS:
        rec = by_id.get(spec["id"])
        if rec is None:
            raise SystemExit(f"{spec['id']} not in the corpus")
        print(f"{spec['id']}  ({spec['why']})")
        if "question" in spec and rec["question"] != spec["question"]:
            print("  stem: reconstructed detail restored")
            rec["question"] = spec["question"]
            changed_fields.add("question")
        if spec.get("correctAnswer") and rec["correctAnswer"] != spec["correctAnswer"]:
            old = rec["correctAnswer"]
            print(f"  key : {old}. {rec['options'][old][:48]}"
                  f"  ->  {spec['correctAnswer']}. {rec['options'][spec['correctAnswer']][:48]}")
            rec["correctAnswer"] = spec["correctAnswer"]
            changed_fields.add("correctAnswer")
        if spec.get("explanation"):
            expl[spec["id"]] = {"text": spec["explanation"], "ai": True, "corrected": True}
            print("  expl: rewritten")

    print(f"\nfields changed: {sorted(changed_fields)}")
    print(dataio.save_master(records, changed_fields=sorted(changed_fields),
                             original=original, dry_run=dry))
    print(dataio.regen_public(records, dry_run=dry))
    print(dataio.save_explanations(expl, dry_run=dry))
    if dry:
        print("\nDRY RUN — nothing written. Re-run with --commit.")


if __name__ == "__main__":
    main()
