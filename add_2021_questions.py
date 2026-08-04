"""
Adds NEET PG 2021 questions to the dataset, filling a year the original
extraction pipeline had to skip entirely (the official 2021 paper was a
scanned-image PDF, not extractable text).

Source: a clean text-based PDF of the 2021 paper (with worked explanations)
from nishantbhushan.in/neetpgquestionpapers. This script downloads it fresh,
parses question/options/answer/explanation blocks out of the extracted text,
filters out the minority of questions that reference an image (their answer
isn't recoverable from text alone), and merges the rest into the app's data
files. Re-running it is a no-op protected by the ID-collision assert below.
"""
import json
import re
import urllib.request

from pypdf import PdfReader

PDF_URL = "https://www.nishantbhushan.in/_files/ugd/37999e_086d33f1c86d4f638c453b8919f2f98c.pdf?index=true"
PDF_LOCAL_PATH = "/tmp/neetpg_2021_source.pdf"

RAW_QUESTIONS_PATH = "data/extracted/questions.json"
PUBLIC_QUESTIONS_PATH = "medico-app/public/questions.json"
EXPLANATIONS_PATH = "medico-app/public/explanations.json"

YEAR = 2021
SHIFT = 1

SUBJECTS = [
    'Anatomy', 'Physiology', 'Biochemistry', 'Pathology', 'Pharmacology',
    'Microbiology', 'Medicine', 'Surgery', 'Obstetrics & Gynaecology',
    'Paediatrics', 'Psychiatry', 'Radiology', 'Orthopaedics', 'ENT',
    'Ophthalmology', 'Dermatology', 'Anaesthesia', 'Forensic Medicine',
    'Community Medicine', 'General Medicine',
]
# Header abbreviations observed in the source PDF -> canonical app subject names
SUBJECT_ALIASES = {
    'Anesthesia': 'Anaesthesia',
    'Forensic': 'Forensic Medicine',
    'Ortho': 'Orthopaedics',
    'Orthopedics': 'Orthopaedics',
    'Pediatric': 'Paediatrics',
    'Pediatrics': 'Paediatrics',
    'Peds': 'Paediatrics',
    'PSM': 'Community Medicine',
    'Skin': 'Dermatology',
    'Obs Gyn': 'Obstetrics & Gynaecology',
    'Obs & Gyn': 'Obstetrics & Gynaecology',
    'Obs/Gyne': 'Obstetrics & Gynaecology',
    'Obs/Gyn': 'Obstetrics & Gynaecology',
    'OBG': 'Obstetrics & Gynaecology',
    'ObsGyn': 'Obstetrics & Gynaecology',
}
ALL_HEADER_NAMES = SUBJECTS + list(SUBJECT_ALIASES.keys())
SUBJECT_LINE_RE = re.compile(r'^(' + '|'.join(re.escape(s) for s in ALL_HEADER_NAMES) + r')\s*$', re.MULTILINE)
WATERMARK_RE = re.compile(r'MEDICAL[\s-]*JUNCTION\.?COM\s*MEDICAL\s*JUNCTION\s*TEAM', re.IGNORECASE)
Q_START_RE = re.compile(r'\n\s*(\d{1,3})\.\s+', re.MULTILINE)
OPT_RE = re.compile(r'\n?\s*([A-D])\.\s+(.*?)(?=\n\s*[A-D]\.\s+|\n\s*Answer|\Z)', re.DOTALL)
ANSWER_RE = re.compile(r'Answer\s*[:<]?\s*\(?([A-D])\)?[:.]?')
EXPLANATION_RE = re.compile(r'Explanation\s*:?\s*(.*)', re.DOTALL)


def canonical_subject(raw: str) -> str:
    return SUBJECT_ALIASES.get(raw, raw)


def make_question_id(year: int, shift: int, q_num: int) -> str:
    return f"neetpg-{year}-s{shift}-q{q_num:04d}"


def download_pdf() -> None:
    req = urllib.request.Request(PDF_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp, open(PDF_LOCAL_PATH, "wb") as f:
        f.write(resp.read())


def extract_text() -> str:
    reader = PdfReader(PDF_LOCAL_PATH)
    full = "\n".join((p.extract_text() or "") for p in reader.pages)
    return WATERMARK_RE.sub("", full)


def parse(text: str) -> list[dict]:
    matches = list(Q_START_RE.finditer(text))
    records = []
    current_subject = None

    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end]

        gap_start = matches[i - 1].end() if i > 0 else 0
        gap = text[gap_start:m.start()]
        subj_matches = SUBJECT_LINE_RE.findall(gap)
        if subj_matches:
            current_subject = canonical_subject(subj_matches[-1])

        opts = {}
        first_opt_pos = None
        for om in OPT_RE.finditer(block):
            letter, otext = om.group(1), re.sub(r'\s+', ' ', om.group(2).strip())
            if letter not in opts:
                opts[letter] = otext
                if first_opt_pos is None:
                    first_opt_pos = om.start()

        question_text = block[:first_opt_pos].strip() if first_opt_pos else block.strip()
        question_text = re.sub(r'\s+', ' ', question_text)

        ans_m = ANSWER_RE.search(block)
        answer = ans_m.group(1) if ans_m else None

        exp_m = EXPLANATION_RE.search(block)
        if exp_m:
            explanation = exp_m.group(1).strip()
        elif ans_m:
            explanation = block[ans_m.end():].strip()
        else:
            explanation = ''
        explanation = re.sub(r'[ \t]+', ' ', explanation).strip()

        records.append({
            'subject': current_subject,
            'question': question_text,
            'options': opts,
            'correctAnswer': answer,
            'explanation': explanation,
        })
    return records


def main() -> None:
    print("Downloading source PDF...")
    download_pdf()
    text = extract_text()
    parsed = parse(text)
    print(f"Parsed {len(parsed)} raw blocks")

    # Keep only fully-parsed questions: a real answer letter, all 4 options,
    # non-trivial question text and explanation. The minority that reference
    # an image (answer not recoverable from text alone) are excluded here.
    clean = [
        r for r in parsed
        if r["correctAnswer"]
        and len(r["options"]) == 4
        and len(r["question"].strip()) >= 5
        and r["explanation"].strip()
    ]
    print(f"{len(clean)} clean questions to add")

    new_raw_questions = []
    new_public_questions = []
    new_explanations = {}

    for i, r in enumerate(clean, start=1):
        qid = make_question_id(YEAR, SHIFT, i)
        base = {
            "id": qid,
            "year": YEAR,
            "shift": SHIFT,
            "questionNumber": i,
            "question": r["question"],
            "options": r["options"],
            "correctAnswer": r["correctAnswer"],
            "subject": r["subject"],
            "topic": "",
            "difficulty": "Easy",
            "tags": [],
        }
        new_raw_questions.append({**base, "explanation": r["explanation"]})
        new_public_questions.append(base)
        new_explanations[qid] = {"text": r["explanation"]}

    raw_questions = json.load(open(RAW_QUESTIONS_PATH))
    existing_ids = {q["id"] for q in raw_questions}
    assert not any(q["id"] in existing_ids for q in new_raw_questions), (
        "2021 questions already present — this script has likely already been run."
    )
    raw_questions.extend(new_raw_questions)
    json.dump(raw_questions, open(RAW_QUESTIONS_PATH, "w"), indent=2, ensure_ascii=False)

    public_questions = json.load(open(PUBLIC_QUESTIONS_PATH))
    public_questions.extend(new_public_questions)
    json.dump(public_questions, open(PUBLIC_QUESTIONS_PATH, "w"), ensure_ascii=False, separators=(",", ":"))

    explanations = json.load(open(EXPLANATIONS_PATH))
    explanations.update(new_explanations)
    json.dump(explanations, open(EXPLANATIONS_PATH, "w"), ensure_ascii=False, separators=(",", ":"))

    print(f"Added {len(clean)} questions for {YEAR} shift {SHIFT}")
    print(f"Total questions now: {len(public_questions)}")
    print(f"Total explanations now: {len(explanations)}")


if __name__ == "__main__":
    main()
