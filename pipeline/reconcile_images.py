"""Point every question at an image that actually exists.

74 of 434 image references were dangling: the file named in `imageUrl` was not on
disk, so the app and every PDF rendered a broken image. The cause is that
`data/pdfs/` is gitignored, so `extract_images.py` was never re-run in this
environment after the corpus moved.

With the source papers fetched and the extractor re-run, this script makes the
corpus agree with the filesystem:

  * copies newly extracted images into the directory the app serves
  * rebuilds `imageUrl`/`imageUrls` from the extractor's map, which is authoritative
    (filenames embed a PDF xref that changes between extraction runs, so the old
    stored paths cannot simply be matched up)
  * drops any reference that still points at nothing, so nothing renders broken
  * never deletes an image already on disk that no question claims

Image fields live only in the app copy, never in the master, so this writes through
`dataio.regen_public`.

Usage:
    python3 -m pipeline.reconcile_images --dry-run
    python3 -m pipeline.reconcile_images --commit
"""
from __future__ import annotations

import argparse
import collections
import json
import shutil

from . import dataio, paths

EXTRACTED_DIR = paths.REPO / "data/images"
IMAGE_MAP = paths.REPO / "data/extracted/image_map.json"
SERVED_PREFIX = "/question-images/"


def load_map() -> dict[str, list[str]]:
    if not IMAGE_MAP.exists():
        return {}
    with open(IMAGE_MAP) as f:
        raw = json.load(f)
    # The extractor writes paths as "images/<paper>/<file>"; the app serves them
    # from "/question-images/<paper>/<file>".
    out: dict[str, list[str]] = {}
    for qid, paths_ in raw.items():
        if isinstance(paths_, str):
            paths_ = [paths_]
        out[qid] = [SERVED_PREFIX + p.split("images/", 1)[-1] for p in paths_]
    return out


def copy_new_images(dry_run: bool) -> int:
    copied = 0
    if not EXTRACTED_DIR.exists():
        return 0
    for src in sorted(EXTRACTED_DIR.rglob("*.png")):
        rel = src.relative_to(EXTRACTED_DIR)
        dest = paths.QUESTION_IMAGES / rel
        if dest.exists() and dest.stat().st_size == src.stat().st_size:
            continue
        copied += 1
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
    return copied


def exists(url: str, *, staged: bool = False) -> bool:
    """Is this image available?

    On a dry run the copy has not happened yet, so a freshly extracted file would
    look missing and every recovered question would be reported as dropped. So the
    staging directory counts as available while previewing.
    """
    if (paths.PUBLIC / url.lstrip("/")).exists():
        return True
    if staged:
        rel = url[len(SERVED_PREFIX):] if url.startswith(SERVED_PREFIX) else url.lstrip("/")
        return (EXTRACTED_DIR / rel).exists()
    return False


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--commit", action="store_true")
    args = ap.parse_args()
    dry = args.dry_run

    copied = copy_new_images(dry)
    print(f"images copied into {paths.QUESTION_IMAGES.relative_to(paths.REPO)}: {copied}")

    fresh = load_map()
    print(f"extractor map covers {len(fresh)} questions")

    with open(paths.PUBLIC_QUESTIONS) as f:
        public = json.load(f)

    recovered = kept = dropped = 0
    per_paper: collections.Counter = collections.Counter()
    still_missing: list[str] = []

    for rec in public:
        old = ([rec["imageUrl"]] if rec.get("imageUrl") else []) + list(rec.get("imageUrls") or [])
        if not old and rec["id"] not in fresh:
            continue
        paper = f"{rec['year']}_s{rec['shift']}"

        # Prefer the extractor's list; fall back to whatever already resolves.
        candidate = fresh.get(rec["id"]) or old
        good = [u for u in candidate if exists(u, staged=dry)]

        was_broken = any(not exists(u, staged=dry) for u in old)
        if good:
            if was_broken:
                recovered += 1
                per_paper[paper] += 1
            else:
                kept += 1
            rec["imageUrl"] = good[0]
            if len(good) > 1:
                rec["imageUrls"] = good[1:]
            else:
                rec.pop("imageUrls", None)
        elif old:
            dropped += 1
            still_missing.append(rec["id"])
            rec.pop("imageUrl", None)
            rec.pop("imageUrls", None)

    total_refs = sum(1 + len(r.get("imageUrls") or []) for r in public if r.get("imageUrl"))
    bad = sum(1 for r in public
              for u in ([r["imageUrl"]] if r.get("imageUrl") else []) + list(r.get("imageUrls") or [])
              if not exists(u, staged=dry))

    print(f"\nquestions with a working image : {sum(1 for r in public if r.get('imageUrl'))}")
    print(f"  recovered (were broken)      : {recovered}")
    print(f"  already fine                 : {kept}")
    print(f"  dropped (still no file)      : {dropped}")
    print(f"image references now dangling  : {bad} of {total_refs}")
    if per_paper:
        print("\nrecovered by paper:")
        for paper, n in sorted(per_paper.items()):
            print(f"  {paper}: {n}")
    if still_missing:
        print(f"\nstill imageless: {', '.join(still_missing[:8])}"
              + (" ..." if len(still_missing) > 8 else ""))

    if dry:
        print("\nDRY RUN — nothing written. Re-run with --commit.")
        return

    tmp = paths.PUBLIC_QUESTIONS.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(public, f, ensure_ascii=False, separators=(",", ":"))
    with open(tmp) as f:
        json.load(f)
    tmp.replace(paths.PUBLIC_QUESTIONS)
    print(f"\nwritten to {paths.PUBLIC_QUESTIONS.relative_to(paths.REPO)}")


if __name__ == "__main__":
    main()
