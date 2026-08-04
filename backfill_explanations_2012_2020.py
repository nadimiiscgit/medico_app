"""
Backfills clean explanations for every PYQ question in 2012-2016/2018-2020
whose current explanation is still a garbled OCR fragment (non-AI-flagged
in medico-app/public/explanations.json).

correct_2012_2020_answers.py already built (and validated) a parser for
these years' source PDFs and matched them against a *flagged* subset to
fix answers/options. Those same parsed PDFs contain a clean explanation for
every question in the paper, not just the previously-flagged ones -- this
script extends the same matching (question number + text similarity) to
every question in these years, but only ever touches explanation text.

Safety: if a match's answer disagrees with the existing (already-verified)
answer, it's excluded and reported rather than applied -- this pass is
explanation-only. In practice this catches rare cases where the source PDF
has two near-identical question stems with different options (e.g. two
"Cephalic phase of gastric secretion?" questions asking different things),
which can fool a text-only similarity match into picking the wrong twin.
"""
import json
import difflib
from collections import defaultdict

from correct_2012_2020_answers import YEAR_PDF_URLS, download_pdf, parse_pdf

RAW_QUESTIONS_PATH = "data/extracted/questions.json"
PUBLIC_QUESTIONS_PATH = "medico-app/public/questions.json"
EXPLANATIONS_PATH = "medico-app/public/explanations.json"
SIMILARITY_THRESHOLD = 0.55


def norm(s: str) -> str:
    return " ".join((s or "").lower().split())


def similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def main() -> None:
    questions = json.load(open(PUBLIC_QUESTIONS_PATH))
    explanations = json.load(open(EXPLANATIONS_PATH))

    targets_by_year = defaultdict(list)
    for q in questions:
        if q["year"] in YEAR_PDF_URLS and not explanations.get(q["id"], {}).get("ai"):
            targets_by_year[q["year"]].append(q)
    print(f"{sum(len(v) for v in targets_by_year.values())} non-AI explanations targeted")

    applied, no_match, answer_mismatch = 0, [], []

    for year in YEAR_PDF_URLS:
        print(f"Downloading and parsing {year}...")
        pdf_path = download_pdf(year)
        parsed = parse_pdf(pdf_path)
        parsed_by_num = defaultdict(list)
        for p in parsed:
            parsed_by_num[p["questionNumber"]].append(p)

        for q in targets_by_year[year]:
            qnum = q["questionNumber"]
            best, best_sim = None, -1
            for offset in range(-5, 6):
                for cand in parsed_by_num.get(qnum + offset, []):
                    sim = similarity(q["question"], cand["question"])
                    if sim > best_sim:
                        best_sim, best = sim, cand

            if best is None or best_sim < SIMILARITY_THRESHOLD:
                no_match.append(q["id"])
                continue
            if best["correctAnswer"] != q["correctAnswer"]:
                answer_mismatch.append((q["id"], q["correctAnswer"], best["correctAnswer"], best_sim))
                continue
            if best["explanation"]:
                explanations[q["id"]] = {"text": best["explanation"]}
                applied += 1

    print(f"\nApplied: {applied}, no confident match: {len(no_match)}, "
          f"answer mismatch (excluded): {len(answer_mismatch)}")
    for qid, old_a, new_a, sim in answer_mismatch:
        print(" ", qid, "old:", old_a, "new:", new_a, "sim:", round(sim, 3))

    json.dump(explanations, open(EXPLANATIONS_PATH, "w"), ensure_ascii=False, separators=(",", ":"))

    raw_questions = json.load(open(RAW_QUESTIONS_PATH))
    synced = 0
    for q in raw_questions:
        e = explanations.get(q["id"])
        if e and q.get("explanation") != e["text"]:
            q["explanation"] = e["text"]
            synced += 1
    json.dump(raw_questions, open(RAW_QUESTIONS_PATH, "w"), indent=2, ensure_ascii=False)
    print(f"Synced {synced} entries into {RAW_QUESTIONS_PATH}")


if __name__ == "__main__":
    main()
