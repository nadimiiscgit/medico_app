#!/usr/bin/env python3
"""
Post-process practice_questions.json:
  1. Normalise subject names to match PYQ naming exactly
  2. Remove Dental questions (not in NEET PG scope)
  3. Re-index IDs after removal
"""

import json
from pathlib import Path

INPUT  = Path("data/extracted/practice_questions.json")
OUTPUT = Path("data/extracted/practice_questions.json")

# Canonical subject names taken from PYQ dataset
SUBJECT_NORMALISE = {
    # OBG variants → PYQ canonical
    "Gynaecology & Obstetrics":       "Obstetrics & Gynaecology",
    "Obstetrics and Gynaecology":     "Obstetrics & Gynaecology",
    "Gynecology & Obstetrics":        "Obstetrics & Gynaecology",
    "Obstetrics & Gynecology":        "Obstetrics & Gynaecology",

    # Paediatrics variants
    "Pediatrics":                     "Paediatrics",
    "Paediatrics":                    "Paediatrics",

    # General catch-all
    "General":                        "General Medicine",

    # Already correct — listed for clarity
    "Anatomy":                        "Anatomy",
    "Physiology":                     "Physiology",
    "Biochemistry":                   "Biochemistry",
    "Pathology":                      "Pathology",
    "Pharmacology":                   "Pharmacology",
    "Microbiology":                   "Microbiology",
    "Community Medicine":             "Community Medicine",
    "Surgery":                        "Surgery",
    "Medicine":                       "Medicine",
    "Ophthalmology":                  "Ophthalmology",
    "Forensic Medicine":              "Forensic Medicine",
    "Psychiatry":                     "Psychiatry",
    "Radiology":                      "Radiology",
    "Orthopaedics":                   "Orthopaedics",
    "ENT":                            "ENT",
    "Dermatology":                    "Dermatology",
    "Anaesthesia":                    "Anaesthesia",
}

REMOVE_SUBJECTS = {"Dental"}


def main():
    print(f"Loading {INPUT}...")
    with open(INPUT, encoding="utf-8") as f:
        questions = json.load(f)

    print(f"Total before: {len(questions)}")

    # Track stats
    subject_changes = {}
    removed_subjects = {}
    cleaned = []

    for q in questions:
        subject = q.get("subject", "")

        # Remove unwanted subjects
        if subject in REMOVE_SUBJECTS:
            removed_subjects[subject] = removed_subjects.get(subject, 0) + 1
            continue

        # Normalise subject name
        normalised = SUBJECT_NORMALISE.get(subject, subject)
        if normalised != subject:
            key = f"{subject} → {normalised}"
            subject_changes[key] = subject_changes.get(key, 0) + 1
            q["subject"] = normalised

        cleaned.append(q)

    # Re-index IDs
    for i, q in enumerate(cleaned, start=1):
        q["id"] = f"medmcqa-{i:06d}"
        q["questionNumber"] = i

    print(f"\nSubject renames:")
    for change, count in sorted(subject_changes.items()):
        print(f"  {change}: {count}")

    print(f"\nRemoved subjects:")
    for subj, count in removed_subjects.items():
        print(f"  {subj}: {count} questions removed")

    print(f"\nTotal after: {len(cleaned)}")

    # Final subject breakdown
    subjects = {}
    for q in cleaned:
        s = q["subject"]
        subjects[s] = subjects.get(s, 0) + 1

    print(f"\nFinal subject distribution:")
    for s, c in sorted(subjects.items(), key=lambda x: -x[1]):
        print(f"  {s}: {c}")

    print(f"\nWriting {OUTPUT}...")
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)

    size_mb = OUTPUT.stat().st_size / 1_000_000
    print(f"Done! {OUTPUT} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
