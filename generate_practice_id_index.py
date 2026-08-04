"""
Build an id -> subject index for all practice questions.

Practice question IDs (medmcqa-NNNNNN) do not encode which subject file they
live in, and are interleaved across the 20 practice_<Subject>.json files. The
app's "jump to question by ID" feature needs to know which file to lazy-load
for a given ID, so this script produces that lookup table once, ahead of time.

Output: medico-app/public/practice_id_index.json  ({ id: subject })
"""

import json
from pathlib import Path

PUBLIC_DIR = Path(__file__).parent / "medico-app" / "public"
OUTPUT = PUBLIC_DIR / "practice_id_index.json"


def main() -> None:
    index: dict[str, str] = {}
    for path in sorted(PUBLIC_DIR.glob("practice_*.json")):
        questions = json.loads(path.read_text())
        subject = questions[0]["subject"] if questions else None
        for q in questions:
            index[q["id"]] = q["subject"]
        print(f"  {path.name}  →  {len(questions):,} questions  (subject: {subject})")

    OUTPUT.write_text(json.dumps(index, separators=(",", ":")))
    size_mb = OUTPUT.stat().st_size / (1024 * 1024)
    print(f"Wrote {len(index):,} entries to {OUTPUT}  ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
