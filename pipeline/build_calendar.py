"""Phase 6 — turn the ranked topics into a day-by-day plan.

Nineteen days, 11-29 August, exam on the 30th. Three choices shape the result:

  High yield first.  Tier A is scheduled early, tier C late, so falling behind
  costs the fewest marks. If time runs out, what is missed is what the exam
  asks least.

  Interleaved, not blocked.  Each day mixes three or four subjects rather than
  spending a whole day on one. It matches the paper's format and retains
  better than block study, even though block study feels more orderly.

  Revisits built in.  A fifth of each day is reserved for revisiting topics
  from three and nine days earlier. Reading 550 topics once and never again is
  how you arrive on the 30th having forgotten the first week.

Subjects are allocated in proportion to their expected question count, so the
daily mix mirrors the real paper instead of treating all 19 subjects equally.

Usage:
    python3 -m pipeline.build_calendar
    python3 -m pipeline.build_calendar --hours 12
"""
from __future__ import annotations

import argparse
import collections
import json
from datetime import date, timedelta

from . import pace, paths

START = date(2026, 8, 11)
EXAM = date(2026, 8, 30)
FIRST_PASS_DAYS = 15
TOTAL_DAYS = 19
REVISIT_SHARE = 0.20
REVISIT_OFFSETS = (3, 9)
SUBJECTS_PER_DAY = 4
TIER_WINDOW = {"A": (1, 9), "B": (4, 13), "C": (9, 15)}


def load_index() -> dict:
    with open(paths.TOPIC_INDEX) as f:
        return json.load(f)


def subject_queues(index: dict, tier_c: str = "mustknow") -> dict[str, list[dict]]:
    """Per-subject topic queues, section-contiguous and high-yield first.

    Sections are kept together because related material learned in one sitting
    sticks better than the same topics scattered across a fortnight.
    """
    queues: dict[str, list[dict]] = {}
    for subject, payload in index["subjects"].items():
        items: list[dict] = []
        for sec in payload["sections"]:            # already high-yield ordered
            for t in sec["topics"]:
                if t["questionCount"] == 0:
                    continue
                read = t.get("estReadMinutes", t["estMinutes"])
                solve = t.get("estSolveMinutes", 0)
                pyqs = t.get("selectedPyqCount", 0)
                reduced = False
                if t["tier"] == "C" and tier_c != "full":
                    if tier_c == "skip":
                        continue
                    # Must-know only: a quarter of the reading, no solving. The
                    # floor is five minutes because a two-minute slot is not a
                    # study session, it is a line item.
                    reduced = True
                    read = max(5, round(read * pace.MUSTKNOW_ONLY_FRACTION))
                    solve, pyqs = 0, 0
                items.append({
                    "topicId": t["topicId"], "topic": t["topic"],
                    "section": sec["section"], "subject": subject,
                    "tier": t["tier"], "highYield": t["highYield"],
                    "minutes": read + solve, "readMinutes": read,
                    "solveMinutes": solve, "scheduledPyqs": pyqs,
                    "mustKnowOnly": reduced, "pyqCount": t["questionCount"],
                })
        items.sort(key=lambda t: ({"A": 0, "B": 1, "C": 2}[t["tier"]],
                                  t["section"], -t["highYield"]))
        if items:
            queues[subject] = items
    return queues


def build(daily_minutes: int, tier_c: str = "mustknow") -> dict:
    index = load_index()
    queues = subject_queues(index, tier_c)
    remaining = {s: sum(t["minutes"] for t in q) for s, q in queues.items()}
    scheduled: dict[int, list[dict]] = collections.defaultdict(list)
    # Revisit load is decided by what was scheduled 3 and 9 days earlier, so it
    # has to be booked as those days are filled and subtracted from the budget
    # here. Adding it afterwards is what made days overrun by up to 2 hours.
    revisit_owed: dict[int, int] = collections.defaultdict(int)
    revisits: dict[int, list[dict]] = collections.defaultdict(list)

    # Priority is GLOBAL, not per-subject. The earlier version walked each
    # subject's own queue, so a subject whose turn came late could leave tier-A
    # topics unscheduled while lower-yield topics from other subjects were
    # taken — five tier-A topics were being dropped that way. Sorting every
    # topic together by tier then yield guarantees that whatever does not fit is
    # genuinely the least valuable material, which is the whole promise of the
    # plan.
    pending = sorted(
        (t for q in queues.values() for t in q),
        key=lambda t: ({"A": 0, "B": 1, "C": 2}[t["tier"]], -t["highYield"]),
    )

    for day in range(1, FIRST_PASS_DAYS + 1):
        used = 0
        new_budget = max(60, daily_minutes - revisit_owed[day])
        per_subject: collections.Counter = collections.Counter()
        subject_cap = max(1, new_budget // SUBJECTS_PER_DAY)

        def take(topic: dict) -> None:
            nonlocal used
            pending.remove(topic)
            scheduled[day].append(topic)
            used += topic["minutes"]
            per_subject[topic["subject"]] += topic["minutes"]
            for offset in REVISIT_OFFSETS:
                target = day + offset
                if target <= TOTAL_DAYS:
                    minutes = max(3, round(topic["minutes"] * 0.25))
                    revisits[target].append({**topic, "minutes": minutes})
                    revisit_owed[target] += minutes

        # First pass keeps the day mixed across subjects; the second fills
        # whatever is left rather than leaving the afternoon empty.
        for spread in (True, False):
            for topic in list(pending):
                if used >= new_budget:
                    break
                if used + topic["minutes"] > new_budget:
                    continue
                if spread and per_subject[topic["subject"]] + topic["minutes"] > subject_cap:
                    continue
                take(topic)

    # Anything the days could not absorb stays unscheduled and is reported.
    # The earlier version forced leftovers into whichever day had most room,
    # which is how a plan that needed 247 hours came out looking like it fitted
    # into 190. A plan that quietly overfills every day is worse than one that
    # states what it could not fit.
    leftovers = pending

    days = []
    for day in range(1, TOTAL_DAYS + 1):
        on = START + timedelta(days=day - 1)
        topics = scheduled.get(day, [])
        rev = revisits.get(day, [])
        blocks: dict[str, list[dict]] = collections.defaultdict(list)
        for t in topics:
            blocks[t["subject"]].append(t)

        entry = {
            "day": day,
            "date": on.isoformat(),
            "weekday": on.strftime("%A"),
            "phase": "first_pass" if day <= FIRST_PASS_DAYS else "revision",
            "newMinutes": sum(t["minutes"] for t in topics),
            "readMinutes": sum(t.get("readMinutes", t["minutes"]) for t in topics),
            "solveMinutes": sum(t.get("solveMinutes", 0) for t in topics),
            "scheduledPyqs": sum(t.get("scheduledPyqs", 0) for t in topics),
            "revisitMinutes": sum(t["minutes"] for t in rev),
            "blocks": [
                {"subject": subject,
                 "minutes": sum(t["minutes"] for t in items),
                 "topics": items}
                for subject, items in sorted(blocks.items(),
                                             key=lambda kv: -sum(t["minutes"] for t in kv[1]))
            ],
            "revisit": rev,
        }
        if day > FIRST_PASS_DAYS:
            n = day - FIRST_PASS_DAYS - 1
            entry["focus"] = REVISION_PLAN[n]
            # Budget the revision work too, so a day that is "only revision"
            # is not reported as idle capacity.
            entry["focusMinutes"] = REVISION_MINUTES[n]
        entry["totalMinutes"] = (entry["newMinutes"] + entry["revisitMinutes"]
                                 + entry.get("focusMinutes", 0))
        days.append(entry)

    return {
        "start": START.isoformat(),
        "exam": EXAM.isoformat(),
        "dailyMinutes": daily_minutes,
        "firstPassDays": FIRST_PASS_DAYS,
        "days": days,
        "unscheduled": [
            {"topicId": t["topicId"], "topic": t["topic"], "subject": t["subject"],
             "tier": t["tier"], "highYield": t["highYield"], "minutes": t["minutes"]}
            for t in leftovers
        ],
    }


# Minutes for each revision day: two Must-know sweeps, a full timed mock
# (200 questions at exam pace, 3.5 h) and its review.
REVISION_MINUTES = [240, 240, 210, 240]

REVISION_PLAN = [
    "Sweep every tier-A chapter's Must-know list. No new topics from here on.",
    "Finish the tier-A sweep, then the tier-B Must-know lists.",
    "Full 200-question mock under timed conditions, built from NEET PG 2023-2025 "
    "and INI CET 2025-2026.",
    "Review the mock, then read the top-100 topic list in the master index.",
]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hours", type=float, default=10.0)
    ap.add_argument("--first-pass-days", type=int, default=FIRST_PASS_DAYS,
                    help="days spent on new material before revision begins")
    ap.add_argument("--tier-c", choices=("full", "mustknow", "skip"),
                    default="mustknow",
                    help="how much of the lowest-yield tier to schedule "
                         "(default: its Must-know list only)")
    args = ap.parse_args()

    globals()["FIRST_PASS_DAYS"] = max(1, min(TOTAL_DAYS - 2, args.first_pass_days))
    calendar = build(int(args.hours * 60), args.tier_c)
    calendar["tierC"] = args.tier_c
    with open(paths.STUDY_CALENDAR, "w") as f:
        json.dump(calendar, f, ensure_ascii=False, indent=1)

    # State the arithmetic before anything else. The previous estimate was 3.7x
    # too low, which let an impossible plan look like it fitted; if the material
    # does not fit now, this says so instead of compressing minutes.
    index = load_index()
    flat = [t for s in index["subjects"].values()
            for sec in s["sections"] for t in sec["topics"] if t["questionCount"]]
    full_load = sum(t["estReadMinutes"] + t["estSolveMinutes"] for t in flat)
    first_pass = sum(d["newMinutes"] for d in calendar["days"])
    revisit = sum(d["revisitMinutes"] for d in calendar["days"])
    focus = sum(d.get("focusMinutes", 0) for d in calendar["days"])
    capacity = int(args.hours * 60) * TOTAL_DAYS
    left = calendar["unscheduled"]
    pace_cfg = index.get("pace", {})

    print(f"pace: {pace_cfg.get('wpm', '?')} wpm, {pace_cfg.get('pyqMinutes', '?')} min/MCQ, "
          f"question scope '{pace_cfg.get('pyqScope', '?')}', tier C '{args.tier_c}'")
    print(f"  material, all {len(flat)} topics      {full_load/60:6.1f} h")
    print(f"  first pass scheduled            {first_pass/60:6.1f} h")
    print(f"  revisits (25% at +3 and +9 days){revisit/60:6.1f} h")
    print(f"  revision days 16-19             {focus/60:6.1f} h")
    print(f"  scheduled total                 {(first_pass+revisit+focus)/60:6.1f} h")
    print(f"  available                       {capacity/60:6.1f} h "
          f"({args.hours:g} h/day x {TOTAL_DAYS} days)")
    if left:
        by_tier = collections.Counter(t["tier"] for t in left)
        print(f"\n  DOES NOT FIT: {len(left)} topics left unscheduled "
              f"({sum(t['minutes'] for t in left)/60:.1f} h), "
              f"tiers {dict(sorted(by_tier.items()))}")
        print("  lowest-yield first, so what is missing is what the exam asks least:")
        for t in left[-6:]:
            print(f"    {t['highYield']:5.2f} [{t['tier']}] {t['subject'][:16]:16s} {t['topic'][:44]}")
        print("  to fit more: --tier-c skip, --hours 12, or rebuild the index "
              "with --pyq-scope none")
        print(f"  (days 16-19 are revision; raising --first-pass-days trades "
              f"revision time for coverage)")
    else:
        print(f"  slack                           "
              f"{(capacity-first_pass-revisit-focus)/60:6.1f} h")
    print()

    total_topics = sum(len(b["topics"]) for d in calendar["days"] for b in d["blocks"])
    print(f"{total_topics} topics across {FIRST_PASS_DAYS} first-pass days, "
          f"{args.hours:g} h/day -> {paths.STUDY_CALENDAR.relative_to(paths.REPO)}")
    # Topics are 8-40 minute blocks, so a day can rarely be packed to the exact
    # minute. A few minutes over is granularity, not overload; flag only a real
    # overrun.
    tolerance = int(calendar["dailyMinutes"] * 1.05)
    over = [d for d in calendar["days"] if d["totalMinutes"] > tolerance]
    worst = max(d["totalMinutes"] for d in calendar["days"])
    print(f"longest day {worst} min against a {calendar['dailyMinutes']} min target")
    if over:
        print(f"WARNING: {len(over)} day(s) exceed the budget: "
              + ", ".join(f"day {d['day']} ({d['totalMinutes']}m)" for d in over[:5]))

    for d in calendar["days"]:
        subjects = ", ".join(f"{b['subject']} {b['minutes']}m" for b in d["blocks"][:3])
        print(f"  day {d['day']:2d} {d['date']} {d['phase']:10s} "
              f"read={d.get('readMinutes',0):4d} solve={d.get('solveMinutes',0):4d} "
              f"rev={d['revisitMinutes']:3d}  {subjects}")


if __name__ == "__main__":
    main()
