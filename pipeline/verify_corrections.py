"""Verify, then apply, the answer-key disagreements the chapters flagged.

A chapter flagging a key as wrong is one opinion. Rewriting a stored answer on
that basis alone would be worse than leaving it: a student who studies a
confidently wrong key is worse off than one who studies a question they knew
was disputed. So every flag gets an independent second opinion, and only the
ones confirmed outright are written back.

Four verdicts, and only the first two change anything:

  key_wrong        the stored answer is wrong and one of the four options is
                   right -> correctAnswer is replaced
  explanation_wrong the key is right but the explanation misleads
                   -> explanation is rewritten, key untouched
  question_broken  the stem or options are defective (image lost in the recall,
                   several options equally correct) -> nothing changed, recorded
  key_correct      the flag was a teaching nuance, not an error -> nothing changed

Usage:
    python3 -m pipeline.verify_corrections --emit
    python3 -m pipeline.verify_corrections --apply --dry-run
    python3 -m pipeline.verify_corrections --apply --commit
"""
from __future__ import annotations

import argparse
import collections
import json
import re

from . import dataio, extract_corrections, paths

PACKET_DIR = paths.PACKETS / "verify"
RETURN_DIR = paths.RETURNS / "verify"
PACKET_SIZE = 12

APPLIED = paths.DOCS / "ANSWER-KEY-FIXES.md"


def emit() -> None:
    flags = extract_corrections.collect()
    by_id = {r["id"]: r for r in dataio.load_master()}
    expl = dataio.load_explanations()

    # One entry per question, carrying every note written about it.
    notes: dict[str, list[dict]] = collections.defaultdict(list)
    for f in flags:
        for qid in f["questionIds"]:
            notes[qid].append({"topic": f["topic"], "claim": f["note"]})

    PACKET_DIR.mkdir(parents=True, exist_ok=True)
    RETURN_DIR.mkdir(parents=True, exist_ok=True)
    for stale in PACKET_DIR.glob("*.json"):
        stale.unlink()

    items = []
    for qid, claims in sorted(notes.items()):
        rec = by_id.get(qid)
        if not rec:
            continue
        items.append({
            "id": qid,
            "exam": rec["exam"],
            "year": rec["year"],
            "sourceConfidence": rec.get("sourceConfidence", "official_recall"),
            "subject": rec["subject"],
            "topic": rec.get("topic", ""),
            "question": rec["question"],
            "options": rec["options"],
            "storedAnswer": rec["correctAnswer"],
            "storedExplanation": (expl.get(qid, {}).get("text")
                                  or rec.get("explanation") or "")[:1200],
            "explanationIsMachineWritten": bool(expl.get(qid, {}).get("ai")),
            "claims": claims,
        })

    for n, i in enumerate(range(0, len(items), PACKET_SIZE), start=1):
        name = f"verify-{n:02d}.json"
        packet = {
            "returnPath": str((RETURN_DIR / name).relative_to(paths.REPO)),
            "questions": items[i:i + PACKET_SIZE],
        }
        with open(PACKET_DIR / name, "w") as f:
            json.dump(packet, f, ensure_ascii=False, indent=1)

    print(f"{len(items)} flagged questions -> {(len(items) + PACKET_SIZE - 1)//PACKET_SIZE} "
          f"packets in {PACKET_DIR.relative_to(paths.REPO)}")


VALID_VERDICTS = {"key_wrong", "explanation_wrong", "question_broken", "key_correct"}


def load_verdicts() -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not RETURN_DIR.exists():
        return out
    for ret in sorted(RETURN_DIR.glob("*.json")):
        with open(ret) as f:
            payload = json.load(f)
        rows = payload if isinstance(payload, list) else payload.get("verdicts", [])
        for row in rows:
            if row.get("verdict") in VALID_VERDICTS and row.get("id"):
                out[row["id"]] = row
    return out


def apply(dry_run: bool) -> None:
    verdicts = load_verdicts()
    if not verdicts:
        raise SystemExit("no verdicts found — run --emit and the verification pass first")

    original = dataio.load_master()
    records = dataio.load_master()
    by_id = {r["id"]: r for r in records}
    expl = dataio.load_explanations()

    changed_keys: list[dict] = []
    changed_expl: list[dict] = []
    skipped: list[dict] = []

    for qid, v in sorted(verdicts.items()):
        rec = by_id.get(qid)
        if not rec:
            continue
        verdict = v["verdict"]
        if verdict == "key_wrong":
            new = (v.get("correctAnswer") or "").strip().upper()
            # Refuse anything that is not one of this question's own options.
            if new not in rec["options"]:
                skipped.append({**v, "reason": f"proposed answer {new!r} is not an option"})
                continue
            if new == rec["correctAnswer"]:
                skipped.append({**v, "reason": "proposed answer equals the stored one"})
                continue
            changed_keys.append({
                "id": qid, "from": rec["correctAnswer"], "to": new,
                "fromText": rec["options"][rec["correctAnswer"]],
                "toText": rec["options"][new],
                "question": rec["question"], "exam": rec["exam"], "year": rec["year"],
                "subject": rec["subject"], "reasoning": v.get("reasoning", ""),
            })
            rec["correctAnswer"] = new
            if v.get("explanation"):
                expl[qid] = {"text": v["explanation"], "ai": True, "corrected": True}
        elif verdict == "explanation_wrong" and v.get("explanation"):
            changed_expl.append({"id": qid, "reasoning": v.get("reasoning", "")})
            expl[qid] = {"text": v["explanation"], "ai": True, "corrected": True}
        else:
            skipped.append({**v, "reason": verdict})

    print(f"answer keys corrected : {len(changed_keys)}")
    print(f"explanations rewritten: {len(changed_expl)}")
    print(f"left alone            : {len(skipped)}")
    by_reason = collections.Counter(s["reason"] for s in skipped)
    for reason, n in by_reason.most_common():
        print(f"    {reason}: {n}")

    print(dataio.save_master(records, changed_fields=["correctAnswer"],
                             original=original, dry_run=dry_run))
    print(dataio.regen_public(records, dry_run=dry_run))
    print(dataio.save_explanations(expl, dry_run=dry_run))

    if not dry_run:
        _write_report(changed_keys, changed_expl, skipped)
    else:
        print("\nDRY RUN — nothing written. Re-run with --commit.")


def _write_report(changed_keys, changed_expl, skipped) -> None:
    lines = [
        "# Answer keys that were corrected",
        "",
        "Each entry below was flagged by a study chapter, then independently",
        "re-examined before anything was changed. Only flags confirmed outright",
        "were applied; teaching nuances and defective questions were left alone.",
        "",
        "The corpus is not authoritative — 41% of its explanations are machine-written",
        "and every paper from 2025 on is a memory-based student recall — which is why",
        "these were worth checking. It follows that this list is not authoritative",
        "either. **Verify anything that matters against your textbook.**",
        "",
        f"**{len(changed_keys)} answer keys changed. {len(changed_expl)} explanations rewritten. "
        f"{len(skipped)} left unchanged.**",
        "",
        "## Answer keys changed",
        "",
    ]
    for c in changed_keys:
        lines += [
            f"### `{c['id']}` — {c['subject']} ({c['exam']} {c['year']})",
            "",
            f"*{c['question'][:220]}*",
            "",
            f"- **Was:** {c['from']}. {c['fromText'][:110]}",
            f"- **Now:** {c['to']}. {c['toText'][:110]}",
            "",
            c["reasoning"],
            "",
        ]
    if changed_expl:
        lines += ["## Explanations rewritten (key was already right)", ""]
        for c in changed_expl:
            lines.append(f"- `{c['id']}` — {c['reasoning'][:200]}")
        lines.append("")
    if skipped:
        lines += ["## Left unchanged", "",
                  "Flagged, examined, and deliberately not altered:", ""]
        for s in skipped:
            lines.append(f"- `{s['id']}` — {s['reason']}. {s.get('reasoning','')[:180]}")

    paths.DOCS.mkdir(parents=True, exist_ok=True)
    APPLIED.write_text("\n".join(lines))
    print(f"\nreport -> {APPLIED.relative_to(paths.REPO)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--emit", action="store_true")
    g.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--commit", action="store_true")
    args = ap.parse_args()

    if args.emit:
        emit()
    else:
        if not (args.dry_run or args.commit):
            raise SystemExit("--apply needs --dry-run or --commit")
        apply(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
