#!/usr/bin/env python3
"""
Split practice_questions.json into one compact JSON file per subject.
Output: medico-app/public/practice_<Subject_Slug>.json
"""
import json, re
from pathlib import Path
from collections import defaultdict

INPUT = Path("data/extracted/practice_questions.json")
OUTPUT_DIR = Path("medico-app/public")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def subject_slug(subject: str) -> str:
    """Must match the TypeScript subjectSlug() function exactly."""
    return re.sub(r'[^A-Za-z0-9]+', '_', subject).strip('_')

print("Loading practice_questions.json...")
questions = json.load(open(INPUT, encoding='utf-8'))
print(f"Total: {len(questions)}")

by_subject = defaultdict(list)
for q in questions:
    by_subject[q['subject']].append(q)

print("\nWriting subject files to medico-app/public/...")
total_size = 0
for subject, qs in sorted(by_subject.items()):
    slug = subject_slug(subject)
    out = OUTPUT_DIR / f"practice_{slug}.json"
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(qs, f, ensure_ascii=False, separators=(',', ':'))
    size = out.stat().st_size / 1_000_000
    total_size += size
    print(f"  practice_{slug}.json  →  {len(qs):,} questions  ({size:.1f} MB)")

print(f"\nTotal: {total_size:.1f} MB across {len(by_subject)} files")
print("Done!")
