#!/usr/bin/env python3
"""
Split explanations out of the per-subject practice files.

The explanation text is ~54% of the practice payload but is only needed once a
user reveals an answer, so shipping it inside the question files makes every
subject load ~3x heavier than it needs to be.

For each medico-app/public/practice_<Slug>.json this writes
practice_expl_<Slug>.json ({id: explanation}) and rewrites the question file
without the explanation field.

Also writes practice_subjects.json — a tiny {subject, count} manifest so the
Question Bank landing grid can show counts without fetching any question data.

Idempotent: re-running after a split is a no-op for already-split files.
"""
import json
import re
from pathlib import Path

PUBLIC_DIR = Path("medico-app/public")


def subject_slug(subject: str) -> str:
    """Must match the TypeScript subjectSlug() function exactly."""
    return re.sub(r'[^A-Za-z0-9]+', '_', subject).strip('_')


def main() -> None:
    files = sorted(
        f for f in PUBLIC_DIR.glob("practice_*.json")
        if not f.name.startswith(("practice_expl_", "practice_id_index", "practice_subjects"))
    )
    if not files:
        raise SystemExit(f"No practice_<Subject>.json files found in {PUBLIC_DIR}")

    manifest = []
    before_total = after_total = expl_total = 0

    for path in files:
        before = path.stat().st_size
        questions = json.loads(path.read_text(encoding="utf-8"))

        explanations = {}
        for q in questions:
            text = q.pop("explanation", None)
            if text:
                explanations[q["id"]] = text

        subject = questions[0]["subject"] if questions else path.stem.replace("practice_", "")
        slug = subject_slug(subject)

        expl_path = PUBLIC_DIR / f"practice_expl_{slug}.json"
        expl_path.write_text(
            json.dumps(explanations, ensure_ascii=False, separators=(',', ':')),
            encoding="utf-8",
        )
        path.write_text(
            json.dumps(questions, ensure_ascii=False, separators=(',', ':')),
            encoding="utf-8",
        )

        after = path.stat().st_size
        expl_size = expl_path.stat().st_size
        before_total += before
        after_total += after
        expl_total += expl_size

        manifest.append({"subject": subject, "count": len(questions)})
        print(
            f"  {path.name:<40} {before/1e6:5.1f} MB -> {after/1e6:5.1f} MB "
            f"(+{expl_size/1e6:4.1f} MB explanations, {len(explanations):,} of {len(questions):,})"
        )

    manifest.sort(key=lambda m: m["subject"])
    manifest_path = PUBLIC_DIR / "practice_subjects.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, separators=(',', ':')),
        encoding="utf-8",
    )

    total_questions = sum(m["count"] for m in manifest)
    print(
        f"\nQuestion files: {before_total/1e6:.1f} MB -> {after_total/1e6:.1f} MB "
        f"({100 * (1 - after_total / before_total):.0f}% smaller)"
    )
    print(f"Explanations split out: {expl_total/1e6:.1f} MB across {len(files)} files")
    print(
        f"Wrote {manifest_path.name}: {len(manifest)} subjects, "
        f"{total_questions:,} questions ({manifest_path.stat().st_size} bytes)"
    )


if __name__ == "__main__":
    main()
