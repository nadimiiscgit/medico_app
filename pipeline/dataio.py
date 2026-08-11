"""Guarded read/write for the question corpus.

The corpus is the one irreplaceable artifact in this repo, and several existing
top-level scripts write it in place with no backup and no verification. Every
pipeline write goes through `save_master` instead, which:

  1. backs the file up first, always;
  2. refuses to write unless the only fields that changed are ones the caller
     declared it was going to change;
  3. writes to a temp file, parses it back to prove it is valid JSON, and only
     then atomically replaces the original.

`regen_public` exists because the app copy is NOT a copy: it drops
`explanation` and carries `imageUrl`/`imageUrls`, which live nowhere else.
Overwriting it with the master (as classify_subjects_llm.py does) silently
destroys the image references for 369 questions.
"""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from typing import Any, Iterable

from . import paths

# Field order used when writing records, so diffs stay readable. Keys absent
# from a record are skipped; keys not listed here are appended alphabetically.
MASTER_ORDER = [
    "id", "source", "exam", "examSession", "sourceConfidence",
    "year", "shift", "questionNumber",
    "question", "options", "correctAnswer", "explanation",
    "subject", "section", "topic", "topicId",
    "difficulty", "tags",
]
PUBLIC_DROP = {"explanation"}
PUBLIC_IMAGE_FIELDS = ("imageUrl", "imageUrls")

Record = dict[str, Any]


def _ordered(rec: Record, drop: Iterable[str] = ()) -> Record:
    drop = set(drop)
    known = [k for k in MASTER_ORDER if k in rec and k not in drop]
    extra = sorted(k for k in rec if k not in MASTER_ORDER and k not in drop)
    return {k: rec[k] for k in known + extra}


def load_master() -> list[Record]:
    with open(paths.QUESTIONS) as f:
        return json.load(f)


def load_explanations() -> dict[str, dict]:
    with open(paths.EXPLANATIONS) as f:
        return json.load(f)


def backup(path=None) -> str:
    """Timestamped copy of the corpus. Returns the backup path."""
    path = path or paths.QUESTIONS
    paths.BACKUPS.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = paths.BACKUPS / f"{path.stem}.{ts}{path.suffix}"
    shutil.copy2(path, dest)
    return str(dest)


def _fingerprint(rec: Record, ignore: set[str]) -> str:
    """Stable hash of every field except the ones the caller may change."""
    subset = {k: v for k, v in rec.items() if k not in ignore}
    return json.dumps(subset, sort_keys=True, ensure_ascii=False)


def _atomic_write_json(path, payload, *, indent: int | None) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as f:
        if indent is None:
            json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
        else:
            json.dump(payload, f, ensure_ascii=False, indent=indent)
    with open(tmp) as f:          # prove it parses before it becomes the real file
        json.load(f)
    os.replace(tmp, path)


def save_master(
    records: list[Record],
    *,
    changed_fields: Iterable[str],
    original: list[Record] | None = None,
    allow_new_ids: bool = False,
    dry_run: bool = False,
) -> dict:
    """Write the corpus, refusing anything the caller did not declare.

    `changed_fields` is the whitelist. If any *other* field of any pre-existing
    record differs from `original`, this raises instead of writing.
    """
    original = original if original is not None else load_master()
    ignore = set(changed_fields)

    old_by_id = {r["id"]: r for r in original}
    new_by_id = {r["id"]: r for r in records}

    if len(new_by_id) != len(records):
        raise ValueError(f"duplicate ids in payload: {len(records)} records, {len(new_by_id)} unique")

    missing = set(old_by_id) - set(new_by_id)
    if missing:
        raise ValueError(f"{len(missing)} existing questions would be dropped, e.g. {sorted(missing)[:5]}")

    added = set(new_by_id) - set(old_by_id)
    if added and not allow_new_ids:
        raise ValueError(f"{len(added)} unexpected new ids, e.g. {sorted(added)[:5]}")

    drifted = [
        qid for qid in old_by_id
        if _fingerprint(old_by_id[qid], ignore) != _fingerprint(new_by_id[qid], ignore)
    ]
    if drifted:
        raise ValueError(
            f"{len(drifted)} records changed outside {sorted(ignore)}, "
            f"e.g. {drifted[:5]} — refusing to write"
        )

    payload = [_ordered(r) for r in records]
    report = {
        "total": len(payload),
        "added": len(added),
        "unchanged_guard": f"{len(old_by_id)} records verified against {sorted(ignore)}",
        "dry_run": dry_run,
    }
    if dry_run:
        return report

    report["backup"] = backup()
    _atomic_write_json(paths.QUESTIONS, payload, indent=2)
    return report


def regen_public(records: list[Record] | None = None, *, dry_run: bool = False) -> dict:
    """Rebuild medico-app/public/questions.json from the master.

    Image fields exist only in the app copy, so they are carried across from
    the current file rather than regenerated. Anything the master no longer has
    is dropped; anything new is picked up.
    """
    records = records if records is not None else load_master()

    images: dict[str, dict] = {}
    if paths.PUBLIC_QUESTIONS.exists():
        with open(paths.PUBLIC_QUESTIONS) as f:
            for rec in json.load(f):
                found = {k: rec[k] for k in PUBLIC_IMAGE_FIELDS if k in rec}
                if found:
                    images[rec["id"]] = found

    payload = []
    for rec in records:
        out = _ordered(rec, drop=PUBLIC_DROP)
        out.update(images.get(rec["id"], {}))
        payload.append(out)

    carried = sum(1 for r in payload if "imageUrl" in r or "imageUrls" in r)
    report = {"total": len(payload), "image_records_carried": carried,
              "image_records_before": len(images), "dry_run": dry_run}

    if carried < len(images):
        raise ValueError(
            f"image references would be lost: {len(images)} before, {carried} after"
        )
    if not dry_run:
        _atomic_write_json(paths.PUBLIC_QUESTIONS, payload, indent=None)
    return report


def save_explanations(expl: dict[str, dict], *, dry_run: bool = False) -> dict:
    report = {"total": len(expl), "dry_run": dry_run}
    if not dry_run:
        report["backup"] = backup(paths.EXPLANATIONS)
        _atomic_write_json(paths.EXPLANATIONS, expl, indent=None)
    return report
