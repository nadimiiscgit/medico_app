"""Download the source question papers into data/pdfs/.

`data/pdfs/` is gitignored — the PDFs are large and not ours to redistribute — so a
fresh clone has none of them. That is why 74 questions across 2022-2024 reference
images that are not on disk: `extract_images.py` never had a paper to extract from.

Filenames match what `extract_images.py`'s PDF_CONFIG expects, so it runs unchanged
afterwards.

Usage:
    python3 -m pipeline.fetch_papers --all
    python3 -m pipeline.fetch_papers --years 2022 2023
"""
from __future__ import annotations

import argparse
import time
import urllib.request

from . import paths

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
BASE = "https://www.nishantbhushan.in/_files/ugd/"

# filename expected by extract_images.py -> source url
PAPERS: dict[str, tuple[str, str]] = {
    "2022": ("FR_neet-pg-2022-question-paper-with-solutions.pdf",
             BASE + "37999e_e1759464937f45c988f8c41df8cf0423.pdf?index=true"),
    "2023": ("FR_neet-pg-2023-question-paper-with-solutions.pdf",
             BASE + "37999e_4ec90f3975124dcfb129a7815048fb19.pdf?index=true"),
    "2024-1": ("FR_neet-pg-2024-shift-1-question-paper.pdf",
               BASE + "37999e_79e0fd35d156402f8b1d8b198ceef37d.pdf?index=true"),
    "2024-2": ("FR_neet-pg-2024-shift-2-question-paper.pdf",
               BASE + "37999e_23cddc70e9364bf7baa07fa1886ee309.pdf?index=true"),
}


def fetch(key: str) -> bool:
    filename, url = PAPERS[key]
    dest = paths.PDFS / filename
    if dest.exists() and dest.stat().st_size > 10_000:
        print(f"  {key:8s} already present ({dest.stat().st_size // 1024} KB)")
        return True
    # The host rate-limits bursts with a 429, so back off rather than give up.
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    data = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = r.read()
            break
        except Exception as e:
            status = getattr(e, "code", None)
            last = f"{type(e).__name__}: {e}"
            if status == 429 and attempt < 4:
                wait = 2 ** (attempt + 2)
                print(f"  {key:8s} rate-limited, retrying in {wait}s")
                time.sleep(wait)
                continue
            print(f"  {key:8s} FAILED: {last}")
            return False
    if data is None:
        return False
    if not data.startswith(b"%PDF"):
        print(f"  {key:8s} FAILED: not a PDF ({len(data)} bytes)")
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    print(f"  {key:8s} -> {filename} ({len(data) // 1024} KB)")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--years", nargs="*", default=[])
    args = ap.parse_args()

    keys = sorted(PAPERS) if args.all else [k for k in sorted(PAPERS)
                                            if any(y in k for y in args.years)]
    if not keys:
        raise SystemExit("nothing selected — pass --all or --years 2022 2023")

    paths.PDFS.mkdir(parents=True, exist_ok=True)
    ok = sum(fetch(k) for k in keys)
    print(f"\n{ok}/{len(keys)} papers available in {paths.PDFS.relative_to(paths.REPO)}")


if __name__ == "__main__":
    main()
