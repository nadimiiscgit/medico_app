#!/usr/bin/env python3
"""Validate the question data the app ships to users.

    python .github/scripts/check_data.py

The app loads these JSON files directly at runtime, so a file that fails to
parse — or a question whose correctAnswer names an option it does not have —
is a broken app, not a broken test. Merges are the usual way that happens:
the practice banks are multi-megabyte single-line files, so a careless
conflict resolution can truncate one without any reviewable diff.

Exit code 0 means the data is safe to ship.
"""

from __future__ import annotations

import glob
import json

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Every question bank the app fetches, and the PYQ source of record.
DATA_GLOBS = ("medico-app/public/*.json", "data/extracted/*.json")

# Files that are question lists rather than lookup tables or reports.
QUESTION_LIST_GLOBS = ("medico-app/public/questions.json",
                       "medico-app/public/practice_*.json")

# practice_id_index.json matches the practice_* glob but is an id lookup table.
NOT_QUESTION_LISTS = {"practice_id_index.json"}

_failures: list[str] = []


def fail(message: str) -> None:
    _failures.append(message)
    print(f"[ FAIL ] {message}")


def ok(message: str) -> None:
    print(f"[  ok  ] {message}")


def load(path: Path):
    """Parse a JSON file, reporting the byte offset if it is malformed."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        rel = path.relative_to(ROOT)
        fail(f"{rel} is not valid JSON: {exc.msg} at byte {exc.pos}")
    except OSError as exc:
        fail(f"{path} could not be read: {exc}")
    return None


def check_parses() -> dict[Path, object]:
    print("\n== JSON parses ==")
    parsed: dict[Path, object] = {}
    for pattern in DATA_GLOBS:
        for name in sorted(glob.glob(str(ROOT / pattern))):
            path = Path(name)
            data = load(path)
            if data is not None:
                parsed[path] = data
    if not parsed:
        fail("no data files found — has the layout moved?")
    elif not _failures:
        ok(f"{len(parsed)} data files parse")
    return parsed


def check_questions(parsed: dict[Path, object]) -> None:
    """Each question needs a unique id and an answer that exists."""
    print("\n== question integrity ==")
    targets = set()
    for pattern in QUESTION_LIST_GLOBS:
        targets.update(
            Path(p)
            for p in glob.glob(str(ROOT / pattern))
            if Path(p).name not in NOT_QUESTION_LISTS
        )

    for path in sorted(targets):
        data = parsed.get(path)
        if data is None:
            continue  # already reported as a parse failure
        rel = path.relative_to(ROOT)
        if not isinstance(data, list):
            fail(f"{rel} should be a list of questions, got {type(data).__name__}")
            continue

        seen: set[str] = set()
        duplicates: set[str] = set()
        bad_answers = 0
        missing_fields = 0

        for question in data:
            if not isinstance(question, dict):
                missing_fields += 1
                continue
            qid = question.get("id")
            options = question.get("options")
            answer = question.get("correctAnswer")

            if not qid or not isinstance(options, dict) or not question.get("question"):
                missing_fields += 1
                continue
            if qid in seen:
                duplicates.add(qid)
            seen.add(qid)

            # options is keyed by letter ({"A": "...", "B": "..."}) and
            # correctAnswer names one of those keys.
            if not isinstance(answer, str) or answer not in options:
                bad_answers += 1

        if missing_fields:
            fail(f"{rel}: {missing_fields} question(s) missing id, question, or options")
        if duplicates:
            sample = ", ".join(sorted(duplicates)[:5])
            fail(f"{rel}: {len(duplicates)} duplicate id(s) — e.g. {sample}")
        if bad_answers:
            fail(f"{rel}: {bad_answers} question(s) whose correctAnswer has no such option")
        if not (missing_fields or duplicates or bad_answers):
            ok(f"{rel}: {len(data)} questions, ids unique, answers in range")


def check_explanations(parsed: dict[Path, object]) -> None:
    """Explanations are keyed by question id — orphans mean a bad merge."""
    print("\n== explanations ==")
    questions = parsed.get(ROOT / "medico-app/public/questions.json")
    explanations = parsed.get(ROOT / "medico-app/public/explanations.json")
    if questions is None or explanations is None:
        ok("skipped — questions.json or explanations.json absent")
        return
    if not isinstance(explanations, dict):
        fail(f"explanations.json should be an object, got {type(explanations).__name__}")
        return

    ids = {q["id"] for q in questions if isinstance(q, dict) and q.get("id")}
    orphans = set(explanations) - ids
    if orphans:
        sample = ", ".join(sorted(orphans)[:5])
        fail(f"explanations.json: {len(orphans)} key(s) match no question — e.g. {sample}")
    else:
        ok(f"all {len(explanations)} explanation keys map to a real question")


def main() -> int:
    parsed = check_parses()
    check_questions(parsed)
    check_explanations(parsed)
    print(f"\n{len(_failures)} failure(s)")
    return 1 if _failures else 0


if __name__ == "__main__":
    sys.exit(main())
