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

from . import paths

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


def subject_queues(index: dict) -> dict[str, list[dict]]:
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
                items.append({
                    "topicId": t["topicId"], "topic": t["topic"],
                    "section": sec["section"], "subject": subject,
                    "tier": t["tier"], "highYield": t["highYield"],
                    "minutes": t["estMinutes"], "pyqCount": t["questionCount"],
                })
        items.sort(key=lambda t: ({"A": 0, "B": 1, "C": 2}[t["tier"]],
                                  t["section"], -t["highYield"]))
        if items:
            queues[subject] = items
    return queues


def build(daily_minutes: int) -> dict:
    index = load_index()
    queues = subject_queues(index)
    remaining = {s: sum(t["minutes"] for t in q) for s, q in queues.items()}
    scheduled: dict[int, list[dict]] = collections.defaultdict(list)
    # Revisit load is decided by what was scheduled 3 and 9 days earlier, so it
    # has to be booked as those days are filled and subtracted from the budget
    # here. Adding it afterwards is what made days overrun by up to 2 hours.
    revisit_owed: dict[int, int] = collections.defaultdict(int)
    revisits: dict[int, list[dict]] = collections.defaultdict(list)

    for day in range(1, FIRST_PASS_DAYS + 1):
        used = 0
        new_budget = max(60, daily_minutes - revisit_owed[day])

        def take(nxt: dict, subject: str) -> None:
            nonlocal used
            queues[subject].pop(0)
            scheduled[day].append(nxt)
            used += nxt["minutes"]
            remaining[subject] -= nxt["minutes"]
            for offset in REVISIT_OFFSETS:
                target = day + offset
                if target <= TOTAL_DAYS:
                    minutes = max(3, round(nxt["minutes"] * 0.25))
                    revisits[target].append({**nxt, "minutes": minutes})
                    revisit_owed[target] += minutes

        # Three passes, the first respecting each tier's window so tier A is
        # genuinely front-loaded, the later ones relaxing constraints only if
        # the day is still short — an empty afternoon in week one is a worse
        # outcome than starting tier B three days early. Three passes, each relaxing one constraint only if the day is still
        # short. Total first-pass reading is 113 h against 150 h of first-pass
        # capacity, so the material does fit — leaving a day underfilled just
        # pushes work into an impossible day 15.
        for respect_window, cap_per_subject in ((True, True), (False, True), (False, False)):
            if used >= new_budget * 0.95:
                break
            # Subjects with the most work left go first, so heavy subjects are
            # spread across the fortnight instead of piling up at the end.
            order = sorted(queues, key=lambda s: -remaining[s])
            picked_subjects = 0
            for subject in order:
                if used >= new_budget or (cap_per_subject and picked_subjects >= SUBJECTS_PER_DAY):
                    break
                queue = queues[subject]
                if not queue:
                    continue
                share = max(1, new_budget // SUBJECTS_PER_DAY) if cap_per_subject else new_budget
                spent = 0
                took = False
                while queue:
                    nxt = queue[0]
                    if respect_window and day < TIER_WINDOW[nxt["tier"]][0]:
                        break
                    # Stop before overshooting rather than after — but never
                    # leave a day completely empty.
                    if used + nxt["minutes"] > new_budget and used > 0:
                        break
                    if spent + nxt["minutes"] > share and spent > 0:
                        break
                    take(nxt, subject)
                    spent += nxt["minutes"]
                    took = True
                if took:
                    picked_subjects += 1

    # Whatever the per-day caps could not absorb is spread into the days with
    # the most room left, rather than dumped on the last day — which produced a
    # 14-hour day 15 while day 11 sat two hours under budget.
    leftovers = [t for q in queues.values() for t in q]
    if leftovers:
        def spare(day: int) -> int:
            used_new = sum(t["minutes"] for t in scheduled[day])
            return daily_minutes - used_new - revisit_owed[day]

        for topic in sorted(leftovers, key=lambda t: {"A": 0, "B": 1, "C": 2}[t["tier"]]):
            day = max(range(1, FIRST_PASS_DAYS + 1), key=spare)
            scheduled[day].append(topic)
            for offset in REVISIT_OFFSETS:
                target = day + offset
                if target <= TOTAL_DAYS:
                    minutes = max(3, round(topic["minutes"] * 0.25))
                    revisits[target].append({**topic, "minutes": minutes})
                    revisit_owed[target] += minutes

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
            entry["focus"] = REVISION_PLAN[day - FIRST_PASS_DAYS - 1]
        entry["totalMinutes"] = entry["newMinutes"] + entry["revisitMinutes"]
        days.append(entry)

    return {
        "start": START.isoformat(),
        "exam": EXAM.isoformat(),
        "dailyMinutes": daily_minutes,
        "firstPassDays": FIRST_PASS_DAYS,
        "days": days,
    }


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
    args = ap.parse_args()

    calendar = build(int(args.hours * 60))
    with open(paths.STUDY_CALENDAR, "w") as f:
        json.dump(calendar, f, ensure_ascii=False, indent=1)

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
        subjects = ", ".join(f"{b['subject']} {b['minutes']}m" for b in d["blocks"][:4])
        print(f"  day {d['day']:2d} {d['date']} {d['phase']:10s} "
              f"new={d['newMinutes']:4d} rev={d['revisitMinutes']:3d}  {subjects}")


if __name__ == "__main__":
    main()
