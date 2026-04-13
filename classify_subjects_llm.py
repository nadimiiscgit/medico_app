"""
LLM-based subject classification for unclassified NEET PG questions.
Uses Claude Haiku to classify questions in batches of 40.
Saves progress after each batch so it can be resumed if interrupted.
"""
import json
import os
import time
import anthropic

SUBJECTS = [
    'Anatomy', 'Physiology', 'Biochemistry', 'Pathology', 'Pharmacology',
    'Microbiology', 'Medicine', 'Surgery', 'Obstetrics & Gynaecology',
    'Paediatrics', 'Psychiatry', 'Radiology', 'Orthopaedics', 'ENT',
    'Ophthalmology', 'Dermatology', 'Anaesthesia', 'Forensic Medicine',
    'Community Medicine',
]

SYSTEM_PROMPT = f"""You are a medical education expert specializing in NEET PG (Indian postgraduate medical entrance exam) question classification.

Given a list of MCQ questions, classify each one into exactly one of these subjects:
{', '.join(SUBJECTS)}

Rules:
- Choose the PRIMARY subject the question tests, not secondary aspects
- A question about drug dosage/mechanism goes to Pharmacology even if the disease is from another subject
- A question about surgical technique/indication goes to Surgery
- A question about epidemiology/statistics/public health goes to Community Medicine
- Anatomical structure questions → Anatomy; physiological process → Physiology
- If the question is about managing a clinical condition (not surgical), default to Medicine
- Return ONLY a JSON array of objects with "id" and "subject" fields. No explanation text."""

def classify_batch(client: anthropic.Anthropic, batch: list[dict]) -> dict[str, str]:
    """Classify a batch of questions. Returns {question_id: subject}."""

    # Build the question list
    q_list = []
    for q in batch:
        opts = q.get('options', {})
        opts_text = ' | '.join(f"{k}: {v}" for k, v in opts.items() if v)
        q_list.append({
            "id": q['id'],
            "question": q['question'][:300],  # truncate very long questions
            "options": opts_text[:200]
        })

    user_msg = f"Classify these {len(batch)} questions:\n{json.dumps(q_list, ensure_ascii=False)}"

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}]
    )

    text = response.content[0].text.strip()

    # Extract JSON array robustly — strip markdown fences if present
    import re as _re
    text = _re.sub(r'^```(?:json)?\s*', '', text, flags=_re.MULTILINE)
    text = _re.sub(r'\s*```$', '', text, flags=_re.MULTILINE)
    text = text.strip()

    classifications = json.loads(text)
    return {item['id']: item['subject'] for item in classifications}


def main():
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        return

    client = anthropic.Anthropic(api_key=api_key)

    data_path = '/Users/nadims_mac/Desktop/medico_pyq_app/data/extracted/questions.json'
    with open(data_path) as f:
        questions = json.load(f)

    # Only reclassify "General Medicine" fallbacks
    to_classify = [q for q in questions if q['subject'] == 'General Medicine']
    print(f"Questions to classify: {len(to_classify)}")

    BATCH_SIZE = 25
    batches = [to_classify[i:i+BATCH_SIZE] for i in range(0, len(to_classify), BATCH_SIZE)]
    total_batches = len(batches)
    print(f"Total batches: {total_batches} (batch size: {BATCH_SIZE})")
    print(f"Estimated cost: ~${total_batches * 0.002:.2f} (Claude Haiku)\n")

    # Build lookup for fast update
    id_to_q = {q['id']: q for q in questions}

    classified = 0
    errors = 0

    for i, batch in enumerate(batches):
        try:
            results = classify_batch(client, batch)

            for q_id, subject in results.items():
                if subject in SUBJECTS and q_id in id_to_q:
                    id_to_q[q_id]['subject'] = subject
                    classified += 1
                else:
                    # Subject not in valid list or unknown id — keep as General Medicine
                    pass

            pct = (i + 1) / total_batches * 100
            print(f"Batch {i+1}/{total_batches} ({pct:.0f}%) — classified {classified} so far", flush=True)

            # Save progress every 10 batches
            if (i + 1) % 10 == 0:
                with open(data_path, 'w') as f:
                    json.dump(questions, f, ensure_ascii=False, separators=(',', ':'))
                print(f"  [checkpoint saved]", flush=True)

            # Rate limiting: 2 seconds between calls to stay under API limits
            if i < total_batches - 1:
                time.sleep(2)

        except Exception as e:
            errors += 1
            print(f"  ERROR in batch {i+1}: {e}", flush=True)
            time.sleep(5)  # Back off on error
            if errors > 10:
                print("Too many errors, stopping.")
                break

    # Final save
    print(f"\nDone! Classified {classified} questions. Errors: {errors}")
    print("Saving...")

    with open(data_path, 'w') as f:
        json.dump(questions, f, ensure_ascii=False, separators=(',', ':'))

    import shutil
    shutil.copy(
        data_path,
        '/Users/nadims_mac/Desktop/medico_pyq_app/medico-app/public/questions.json'
    )
    print("Copied to public/")

    # Print final distribution
    from collections import Counter
    subj_counts = Counter(q['subject'] for q in questions)
    print("\n=== Final subject distribution ===")
    for s, c in sorted(subj_counts.items(), key=lambda x: -x[1]):
        print(f"  {s}: {c} ({c/len(questions)*100:.1f}%)")


if __name__ == '__main__':
    main()
