"""Phase 0b/0c — ingest memory-based recall papers into the corpus.

Neither NBE nor AIIMS releases papers, so 2025-2026 exists only as student
recalls. Two destinations, decided by whether a recall preserved the options:

  data/extracted/questions.json   full MCQs (stem + 4 options + answer)
  data/extracted/recalls.json     stem + answer only — not answerable as an
                                  MCQ, but it still names the topic, which is
                                  what Phase 3 prioritisation actually needs

Everything ingested here carries sourceConfidence="memory_based" so no
downstream step treats it as an official paper.

Re-running is a no-op: ids are deterministic and colliding ids are skipped.

Usage:
    python3 -m pipeline.ingest_recalls --source inicet2025 --dry-run
    python3 -m pipeline.ingest_recalls --source inicet2025 --commit
    python3 -m pipeline.ingest_recalls --source neetpg2025 --commit
"""
from __future__ import annotations

import argparse
import collections
import json
import urllib.request

from . import dataio, parse_recalls, paths

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"

SOURCES = {
    "inicet2025": {
        "kind": "blog",
        "url": "https://www.diginerve.com/blogs/ini-cet-2025-recall-questions-with-answers-free-pdf-download-all-200-qs/",
        "cache": "inicet_2025.html",
        "header": r"INI-?CET 2025 Recall Questions",
        "exam": "INI CET",
        "year": 2025,
        "shift": 1,
        "prefix": "inicet-2025-s1",
    },
    "inicet2026": {
        "kind": "blog",
        "url": "https://www.diginerve.com/blogs/inicet-may-2026-recall-questions-with-answers-pdf/",
        "cache": "inicet_2026.html",
        "header": r"INI-?CET .*2026 Recall Questions",
        "exam": "INI CET",
        "year": 2026,
        "shift": 1,
        "prefix": "inicet-2026-s1",
    },
    "neetpg2025": {
        "kind": "blog",
        "url": "https://www.diginerve.com/blogs/neet-pg-2025-recall-questions-with-answers-free-pdf-download-all-200-qs/",
        "cache": "neetpg_2025.html",
        "header": r"NEET PG 2025 Recall Questions",
        "exam": "NEET PG",
        "year": 2025,
        "shift": 1,
        "prefix": "neetpg-2025-s1",
    },
    # The same paper as neetpg2025, recalled as a topic table with no options.
    # Kept because its topic column is an independent read on what was asked,
    # and it covers questions the MCQ recall missed. Distinct id prefix so the
    # two versions of the 2025 paper can never collide.
    "neetpg2025_table": {
        "kind": "pgmasters_pdf",
        "url": "https://www.nishantbhushan.in/_files/ugd/37999e_691fe27041df45f58ab17898d4fd2c58.pdf?index=true",
        "cache": "neetpg_2025.pdf",
        "exam": "NEET PG",
        "year": 2025,
        "shift": 1,
        "prefix": "neetpg-2025-recall",
    },
}


def fetch(url: str, dest) -> bytes:
    if dest.exists():
        return dest.read_bytes()
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return data


def load_recalls() -> list[dict]:
    path = paths.REPO / "data/extracted/recalls.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []


def save_recalls(records: list[dict], *, dry_run: bool) -> dict:
    path = paths.REPO / "data/extracted/recalls.json"
    report = {"total": len(records), "dry_run": dry_run}
    if not dry_run:
        if path.exists():
            report["backup"] = dataio.backup(path)
        tmp = path.with_suffix(".json.tmp")
        with open(tmp, "w") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        with open(tmp) as f:
            json.load(f)
        tmp.replace(path)
    return report


def build(source: str) -> tuple[list[dict], list[dict]]:
    """Return (full MCQ records, partial recall records) for one source."""
    cfg = SOURCES[source]
    blob = fetch(cfg["url"], paths.PDFS / cfg["cache"])

    if cfg["kind"] == "blog":
        parsed = parse_recalls.parse_subject_blog(
            blob.decode("utf-8", errors="replace"), cfg["header"]
        )
    else:
        parsed = parse_recalls.parse_pgmasters_table(str(paths.PDFS / cfg["cache"]))

    full, partial = [], []
    for i, rec in enumerate(parsed, start=1):
        qid = f"{cfg['prefix']}-q{i:04d}"
        base = {
            "id": qid,
            "exam": cfg["exam"],
            "sourceConfidence": "memory_based",
            "year": cfg["year"],
            "shift": cfg["shift"],
            "questionNumber": i,
            "question": rec["question"],
            # Left empty rather than defaulted when the source names a topic
            # ("Amniotic Band Syndrome") instead of a subject — Phase 2 resolves
            # it, and a wrong default would silently corrupt the subject counts.
            "subject": rec["subject"],
            "topic": "",
            "difficulty": "Medium",
            "tags": [],
        }
        if rec["complete"]:
            full.append({**base, "options": rec["options"],
                         "correctAnswer": rec["correctAnswer"]})
        else:
            partial.append({**base,
                            "answerText": rec.get("answer", "") or rec.get("correctAnswer", ""),
                            "subjectRaw": rec.get("subjectRaw", "")})
    return full, partial


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", required=True, choices=sorted(SOURCES))
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--commit", action="store_true")
    args = ap.parse_args()
    dry = args.dry_run

    paths.ensure_dirs()
    full, partial = build(args.source)

    print(f"source {args.source}: {len(full)} full MCQs, {len(partial)} partial recalls")
    by_subj = collections.Counter(r["subject"] for r in full + partial)
    for s in sorted(by_subj):
        print(f"  {s:26s} {by_subj[s]}")

    # --- full MCQs into the corpus -----------------------------------------
    original = dataio.load_master()
    existing = {r["id"] for r in original}
    new = [r for r in full if r["id"] not in existing]
    skipped = len(full) - len(new)
    if skipped:
        print(f"\n{skipped} already present — skipping (re-run is a no-op)")

    records = dataio.load_master() + new
    rep = dataio.save_master(
        records,
        changed_fields=[],
        original=original,
        allow_new_ids=True,
        dry_run=dry,
    )
    print(f"master: +{len(new)} -> {rep}")
    pub = dataio.regen_public(records, dry_run=dry)
    print(f"public: {pub}")

    # --- partial recalls into their own file -------------------------------
    recalls = load_recalls()
    have = {r["id"] for r in recalls}
    added = [r for r in partial if r["id"] not in have]
    rrep = save_recalls(recalls + added, dry_run=dry)
    print(f"recalls: +{len(added)} -> {rrep}")

    if dry:
        print("\nDRY RUN — nothing written. Re-run with --commit.")


if __name__ == "__main__":
    main()
