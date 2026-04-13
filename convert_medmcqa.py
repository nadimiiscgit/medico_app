#!/usr/bin/env python3
"""
MedMCQA → medico-app Question converter

Downloads the MedMCQA dataset from HuggingFace (train + validation splits)
and converts it to the same Question schema used by questions.json.

Output: data/extracted/practice_questions.json
"""

import json
import uuid
import re
from pathlib import Path

OUTPUT_PATH = Path("data/extracted/practice_questions.json")
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Subject normalisation — map MedMCQA subject names → app subject names
# ---------------------------------------------------------------------------
SUBJECT_MAP = {
    "Anatomy": "Anatomy",
    "Physiology": "Physiology",
    "Biochemistry": "Biochemistry",
    "Pharmacology": "Pharmacology",
    "Pathology": "Pathology",
    "Microbiology": "Microbiology",
    "Forensic Medicine": "Forensic Medicine",
    "Forensic Medicine and Toxicology": "Forensic Medicine",
    "ENT": "ENT",
    "Ophthalmology": "Ophthalmology",
    "Medicine": "Medicine",
    "Surgery": "Surgery",
    "Pediatrics": "Pediatrics",
    "Obstetrics & Gynaecology": "Obstetrics & Gynaecology",
    "Obstetrics and Gynaecology": "Obstetrics & Gynaecology",
    "Gynecology & Obstetrics": "Obstetrics & Gynaecology",
    "Psychiatry": "Psychiatry",
    "Skin": "Dermatology",
    "Dermatology": "Dermatology",
    "Orthopaedics": "Orthopaedics",
    "Orthopedics": "Orthopaedics",
    "Radiology": "Radiology",
    "Anaesthesia": "Anaesthesia",
    "Anesthesia": "Anaesthesia",
    "Community Medicine": "Community Medicine",
    "Social & Preventive Medicine": "Community Medicine",
    "Respiratory Medicine": "Medicine",
    "Cardiology": "Medicine",
    "Gastroenterology": "Medicine",
    "Neurology": "Medicine",
    "Unknown": "General",
}

OPTION_MAP = {0: "A", 1: "B", 2: "C", 3: "D"}


def normalise_subject(raw: str) -> str:
    if not raw:
        return "General"
    raw = raw.strip()
    return SUBJECT_MAP.get(raw, raw.title())


def clean(text) -> str:
    if not text or (isinstance(text, float)):
        return ""
    return str(text).strip()


def estimate_difficulty(question: str, explanation: str) -> str:
    """Rough heuristic: long question + long explanation → harder."""
    total_len = len(question) + len(explanation)
    if total_len < 300:
        return "Easy"
    elif total_len < 700:
        return "Medium"
    return "Hard"


def convert_row(row, index: int):
    question_text = clean(row.get("question", ""))
    opa = clean(row.get("opa", ""))
    opb = clean(row.get("opb", ""))
    opc = clean(row.get("opc", ""))
    opd = clean(row.get("opd", ""))
    cop = row.get("cop")  # 0-3
    explanation = clean(row.get("exp", ""))
    subject_raw = clean(row.get("subject_name", ""))
    topic = clean(row.get("topic_name", ""))
    choice_type = clean(row.get("choice_type", "single"))

    # Skip multi-select questions (app only supports single correct)
    if choice_type == "multi":
        return None

    # Skip if essential fields missing
    if not question_text or not opa or cop is None:
        return None

    # cop can be float (NaN) in some rows
    try:
        cop_int = int(cop)
    except (ValueError, TypeError):
        return None

    if cop_int not in OPTION_MAP:
        return None

    correct_answer = OPTION_MAP[cop_int]
    subject = normalise_subject(subject_raw)

    return {
        "id": f"medmcqa-{index:06d}",
        "source": "practice",          # distinguishes from PYQ
        "year": 0,                      # no year for practice Qs
        "shift": 0,
        "questionNumber": index,
        "question": question_text,
        "options": {"A": opa, "B": opb, "C": opc, "D": opd},
        "correctAnswer": correct_answer,
        "explanation": explanation,
        "subject": subject,
        "topic": topic,
        "difficulty": estimate_difficulty(question_text, explanation),
        "tags": [],
    }


# ---------------------------------------------------------------------------
# Download & convert
# ---------------------------------------------------------------------------

def download_and_convert():
    try:
        import pandas as pd
        from huggingface_hub import hf_hub_download
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Run: pip3 install pandas pyarrow huggingface_hub")
        return

    splits = ["train", "validation"]
    all_questions = []
    global_index = 1

    for split in splits:
        print(f"\nDownloading {split} split...")
        try:
            path = hf_hub_download(
                repo_id="openlifescienceai/medmcqa",
                repo_type="dataset",
                filename=f"data/{split}-00000-of-00001.parquet",
            )
            print(f"  Downloaded to: {path}")
        except Exception as e:
            print(f"  Failed to download {split}: {e}")
            continue

        print(f"  Converting {split}...")
        df = pd.read_parquet(path)
        print(f"  Rows in {split}: {len(df)}")

        converted = 0
        skipped = 0
        for _, row in df.iterrows():
            q = convert_row(row.to_dict(), global_index)
            if q:
                all_questions.append(q)
                global_index += 1
                converted += 1
            else:
                skipped += 1

        print(f"  Converted: {converted}  Skipped: {skipped}")

    print(f"\nTotal practice questions: {len(all_questions)}")

    # Stats
    subjects = {}
    difficulties = {"Easy": 0, "Medium": 0, "Hard": 0}
    for q in all_questions:
        subjects[q["subject"]] = subjects.get(q["subject"], 0) + 1
        difficulties[q["difficulty"]] = difficulties.get(q["difficulty"], 0) + 1

    print("\nBy subject:")
    for s, c in sorted(subjects.items(), key=lambda x: -x[1])[:15]:
        print(f"  {s}: {c}")

    print("\nBy difficulty:")
    for d, c in difficulties.items():
        print(f"  {d}: {c}")

    print(f"\nWriting to {OUTPUT_PATH}...")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_questions, f, ensure_ascii=False, indent=2)

    size_mb = OUTPUT_PATH.stat().st_size / 1_000_000
    print(f"Done! {OUTPUT_PATH} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    download_and_convert()
