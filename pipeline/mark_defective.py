"""Record questions that are defective as printed, and which answers to accept.

Twelve of the fourteen questions the adjudication marked broken cannot be repaired,
because the fault is in the paper rather than in the stored key. Seven offer two or
more equally correct options, one offers no correct option at all, one has a stem
that contradicts itself, and three lost the evidence the question turns on.

Forcing a "best" answer onto these would invent certainty the paper does not support
and would mark you wrong for choosing an option that is, in fact, correct. So each is
annotated instead: the defect is named, and where more than one option is defensible
they are all recorded so the app can accept any of them.

Every entry below was checked by hand. `acceptableAnswers` always includes the stored
key when the stored key is defensible, so nothing that was already right becomes wrong.

Usage:
    python3 -m pipeline.mark_defective --dry-run
    python3 -m pipeline.mark_defective --commit
"""
from __future__ import annotations

import argparse

from . import dataio

REVIEWED_ON = "2026-08-09"

DEFECTS: dict[str, dict] = {
    # --- two or more options equally correct -------------------------------
    "neetpg-2017-s1-q0068": {
        "defect": "multiple_correct_options",
        # The stored key is Aspergillus, which is simply wrong here, so the default
        # answer has to move as well as the acceptable set being widened. Mucor is
        # the answer these papers conventionally expect; Rhizopus is equally right.
        "setKey": "B",
        "acceptableAnswers": ["B", "D"],
        "note": "Rhino-orbital infection in diabetic ketoacidosis is caused by the "
                "Mucorales, and the paper offers Mucor (B) and Rhizopus (D) as separate "
                "options, so neither can be the single answer. Rhizopus arrhizus is the "
                "commonest species. The stored key, Aspergillus, is wrong for this "
                "presentation.",
    },
    "neetpg-2018-s1-q0093": {
        "defect": "multiple_correct_options",
        "setKey": "B",
        "acceptableAnswers": ["B", "D"],
        "note": "Identical item to the 2017 paper, with the same split: Mucor (B) and "
                "Rhizopus (D) are both Mucorales, and the stored key of Aspergillus is "
                "wrong for rhino-orbital disease in ketoacidosis.",
    },
    "neetpg-2016-s1-q1169": {
        "defect": "multiple_correct_options",
        "acceptableAnswers": ["A", "B"],
        "note": "Tuberous sclerosis is caused by loss-of-function mutations in TSC1 "
                "(hamartin) OR TSC2 (tuberin), and the stem asks for 'proteins' in the "
                "plural. TSC2 mutations are commoner and more severe. Both A and B are "
                "correct as printed.",
    },
    "neetpg-2012-s1-q1156": {
        "defect": "multiple_correct_options",
        "acceptableAnswers": ["C", "D"],
        "note": "Options C ('chromosomal abnormalities') and D ('cytogenetic "
                "abnormalities') are synonyms, so neither can be marked over the other. "
                "Substantively the commonest cause of male pseudohermaphroditism is "
                "androgen insensitivity, which is not offered at all.",
    },
    "neetpg-2019-s1-q0010": {
        "defect": "multiple_correct_options",
        "acceptableAnswers": ["A", "B", "C", "D"],
        "note": "All four options are pharyngeal arch derivatives: anterior belly of "
                "digastric from the first arch, buccinator and stylohyoid from the second, "
                "levator veli palatini from the fourth. The stem has almost certainly lost "
                "the word 'first', for which the stored key would be right. Learn the arch "
                "of all four.",
    },
    "neetpg-2022-s1-q0039": {
        "defect": "multiple_correct_options",
        "acceptableAnswers": ["A", "B"],
        "note": "Ruptured membranes (A) and membranes prolapsed into the vagina (B) are "
                "both absolute contraindications to cervical cerclage, alongside "
                "chorioamnionitis, active labour, bleeding and lethal fetal anomaly.",
    },
    "neetpg-2012-s1-q0660": {
        "defect": "multiple_correct_options",
        "acceptableAnswers": ["A", "B", "C", "D"],
        "note": "Every option is a valid source of nuclear DNA. Dental pulp is one of the "
                "most reliable sources in charred, buried or skeletonised remains and is "
                "standard in disaster victim identification, so the stored key of 'tooth' "
                "is the opposite of the truth.",
    },
    # --- no correct option offered -----------------------------------------
    "neetpg-2013-s1-q0423": {
        "defect": "no_correct_option",
        "note": "Read literally, an affected parent (aa) and a genotypically normal partner "
                "(AA) produce only obligate carriers, so the risk of disease is 0 per cent, "
                "which is not offered. The keyed 50 per cent would be right only if the "
                "'normal' parent were a carrier, which the stem does not say. If a version "
                "of this reappears, read carefully whether the second parent is a carrier.",
    },
    # --- self-contradictory stem -------------------------------------------
    "inicet-2025-s1-q0058": {
        "defect": "contradictory_stem",
        "note": "The stem says 'autosomal recessive mitochondrial disorder'. Primary "
                "mitochondrial DNA disease is maternally inherited and never autosomal "
                "recessive, though nuclear-encoded respiratory-chain defects can be. The "
                "systems classically affected are the ones with the highest energy demand: "
                "brain, skeletal muscle, heart, eye. Memory-based recall, so the stem is "
                "probably garbled.",
    },
    # --- evidence lost ------------------------------------------------------
    "neetpg-2013-s1-q1870": {
        "defect": "evidence_lost",
        "note": "The stem asks you to read an ECG that is absent from this recall, and no "
                "images exist for the 2013 paper in this corpus, so the tracing cannot be "
                "recovered. The stored explanation is incoherent besides: it describes an "
                "irregular rhythm with a fibrillatory baseline, which is atrial fibrillation, "
                "then keys ventricular fibrillation - which has no organised complexes and "
                "is a cardiac arrest, not a palpitations complaint.",
    },
    "neetpg-2024-s1-q0079": {
        "defect": "evidence_lost",
        "note": "The four options survive only as the bare letters C, P, T, T, with T "
                "duplicated. The truncation is present in the source paper itself, not "
                "introduced by extraction, so it cannot be repaired from that source. The "
                "clinical scenario - term pregnancy, arrest at 8 cm, emergency caesarean, "
                "intractable postpartum haemorrhage, emergency hysterectomy - is worth "
                "knowing on its own.",
    },
    # --- genuinely contested -----------------------------------------------
    "neetpg-2025-s1-q0065": {
        "defect": "contested_answer",
        "acceptableAnswers": ["B", "C"],
        "note": "In NON-valvular atrial fibrillation under 48 hours, early cardioversion is "
                "acceptable, which is what the recalled key (B) reflects. But this patient "
                "has mitral stenosis, so the atrium may already hold thrombus that pre-dates "
                "the arrhythmia; in valvular AF the under-48-hour rule does not transfer, and "
                "anticoagulation with rate control, or transoesophageal echo before "
                "cardioversion, is the safer answer. Memory-based recall, so the key itself "
                "is uncertain. Know both positions.",
    },
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
    by_id = {r["id"]: r for r in records}
    moved_keys: list[str] = []

    for qid, spec in DEFECTS.items():
        rec = by_id.get(qid)
        if rec is None:
            raise SystemExit(f"{qid} not in the corpus")
        accept = spec.get("acceptableAnswers")
        if accept:
            bad = [a for a in accept if a not in rec["options"]]
            if bad:
                raise SystemExit(f"{qid}: acceptable answers {bad} are not options")
            set_key = spec.get("setKey")
            if set_key:
                if set_key not in accept:
                    raise SystemExit(f"{qid}: setKey {set_key} is not in {accept}")
                if rec["correctAnswer"] != set_key:
                    print(f"  {qid:24s} key {rec['correctAnswer']} -> {set_key} "
                          f"(stored key was not among the correct options)")
                    rec["correctAnswer"] = set_key
                    moved_keys.append(qid)
            elif rec["correctAnswer"] not in accept:
                raise SystemExit(
                    f"{qid}: the stored key {rec['correctAnswer']} is not in "
                    f"acceptableAnswers {accept} — set an explicit setKey to move it"
                )
        rec["dataQuality"] = {
            "status": "defective",
            "defect": spec["defect"],
            **({"acceptableAnswers": accept} if accept else {}),
            "note": spec["note"],
            "reviewedOn": REVIEWED_ON,
        }
        marker = ("accepts " + "/".join(accept)) if accept else "no answer accepted"
        print(f"  {qid:24s} {spec['defect']:26s} {marker}")

    print(f"\n{len(DEFECTS)} questions marked defective, {len(moved_keys)} keys moved")
    print(dataio.save_master(records, changed_fields=["dataQuality", "correctAnswer"],
                             original=original, dry_run=dry))
    print(dataio.regen_public(records, dry_run=dry))
    if dry:
        print("\nDRY RUN — nothing written. Re-run with --commit.")


if __name__ == "__main__":
    main()
