#!/usr/bin/env python3
"""
NEET PG PDF Question Extractor v2

Improvements over v1:
- Format detection per-PDF via page 0 sample
- Multiple regex patterns tried; picks extractor with best result
- Confidence scoring: high / medium / low
- LLM subject classification (claude-haiku) for questions keyword matching fails on
- Output split: questions.json (high+medium), questions_review.json (low)
- Processes one PDF at a time with progress output
"""

import re
import json
import os
import glob
import signal
from pathlib import Path

import pdfplumber

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

OUTPUT_DIR = Path("data/extracted")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MAIN_OUTPUT   = OUTPUT_DIR / "questions.json"
REVIEW_OUTPUT = OUTPUT_DIR / "questions_review.json"
REPORT_OUTPUT = OUTPUT_DIR / "extraction_report.json"


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'www\.FirstRanker\.com\s*', '', text)
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        line = line.strip()
        if len(line) == 1 and line.lower() in 'mowcreknaRtsFrif.www':
            continue
        cleaned.append(line)
    text = ' '.join(l for l in cleaned if l)
    return re.sub(r'\s{2,}', ' ', text).strip()


def map_answer_letter(ans: str, option_style: str = 'ABCD') -> str:
    ans = ans.strip().upper()
    if option_style == 'numbered':
        return {'1': 'A', '2': 'B', '3': 'C', '4': 'D'}.get(ans, ans)
    if ans in 'ABCD' and len(ans) == 1:
        return ans
    m = re.search(r'\b([ABCD])\b', ans)
    return m.group(1) if m else ans


def infer_difficulty(question: str, options: dict) -> str:
    total_len = len(question) + sum(len(v) for v in options.values())
    if total_len < 200:
        return 'Easy'
    elif total_len < 400:
        return 'Medium'
    return 'Hard'


def make_question_id(year: int, shift: int, q_num: int) -> str:
    return f"neetpg-{year}-s{shift}-q{q_num:04d}"


# ---------------------------------------------------------------------------
# Subject classification
# ---------------------------------------------------------------------------

SUBJECT_KEYWORDS = {
    'Anatomy': ['anatomy', 'anatomical', 'histology', 'embryology', 'nerve supply', 'artery',
                'vein', 'muscle', 'bone', 'vertebra', 'thorax', 'abdomen', 'pelvis', 'limb'],
    'Physiology': ['physiology', 'physiological', 'receptor', 'hormone', 'cardiac output',
                   'membrane potential', 'action potential', 'respiratory rate', 'renal threshold'],
    'Biochemistry': ['biochemistry', 'enzyme', 'metabolism', 'glucose', 'protein synthesis',
                     'dna', 'rna', 'vitamin', 'amino acid', 'fatty acid', 'glycolysis', 'krebs'],
    'Pathology': ['pathology', 'neoplasm', 'carcinoma', 'tumour', 'tumor', 'biopsy',
                  'histopathology', 'granuloma', 'infarction', 'necrosis', 'hyperplasia', 'metaplasia'],
    'Pharmacology': ['pharmacology', 'drug of choice', 'pharmacokinetics', 'agonist', 'antagonist',
                     'side effect', 'toxicity', 'antibiotic', 'antifungal', 'antiviral', 'mechanism of action'],
    'Microbiology': ['microbiology', 'bacteria', 'virus', 'fungus', 'parasite', 'culture media',
                     'gram stain', 'organism', 'infection', 'pathogen', 'serotype'],
    'Forensic Medicine': ['forensic', 'medicolegal', 'autopsy', 'rigor mortis', 'postmortem',
                          'poison', 'hanging', 'drowning', 'ipc'],
    'Preventive & Social Medicine': ['preventive', 'social medicine', 'nsso', 'nhfs',
                                     'national programme', 'malnutrition index'],
    'Community Medicine': ['community medicine', 'epidemiology', 'public health', 'vaccination',
                           'prevalence', 'incidence', 'sensitivity', 'specificity', 'herd immunity'],
    'General Medicine': ['hypertension', 'diabetes', 'thyroid', 'cardiac failure', 'pulmonary',
                         'renal failure', 'anemia', 'lupus', 'rheumatoid', 'hepatitis', 'cirrhosis'],
    'Surgery': ['surgery', 'surgical', 'appendix', 'hernia', 'laparoscopy', 'anastomosis',
                'bowel obstruction', 'colostomy', 'ileostomy', 'cholecystectomy'],
    'Obstetrics & Gynaecology': ['obstetric', 'gynaecology', 'gynecology', 'pregnancy', 'labour',
                                  'cervix', 'uterus', 'ovary', 'fetus', 'placenta', 'amenorrhea'],
    'Paediatrics': ['paediatric', 'pediatric', 'child', 'infant', 'neonatal', 'developmental milestone'],
    'Psychiatry': ['psychiatry', 'psychiatric', 'schizophrenia', 'depression', 'anxiety',
                   'bipolar', 'psychosis', 'dementia', 'cognitive'],
    'Radiology': ['radiology', 'x-ray', 'ct scan', 'mri', 'ultrasound', 'imaging', 'radiograph'],
    'Orthopaedics': ['orthopaedic', 'orthopedic', 'fracture', 'dislocation', 'joint replacement',
                     'osteomyelitis', 'bone tumour'],
    'ENT': [' ent ', 'ear', 'nose', 'throat', 'larynx', 'pharynx', 'tonsil', 'otitis',
            'epistaxis', 'rhinitis', 'sinusitis'],
    'Ophthalmology': ['ophthalmology', 'eye', 'retina', 'glaucoma', 'cataract', 'cornea',
                      'conjunctiva', 'visual acuity'],
    'Dermatology': ['dermatology', 'skin', 'rash', 'psoriasis', 'eczema', 'melanoma',
                    'pemphigus', 'vitiligo', 'alopecia'],
    'Anaesthesia': ['anaesthesia', 'anesthesia', 'sedation', 'intubation', 'spinal block',
                    'epidural', 'local anaesthetic'],
}


def infer_subject_keyword(text: str) -> tuple:
    """Returns (subject, source) where source is 'keyword' or 'needs_llm'."""
    text_lower = text.lower()
    for subject, keywords in SUBJECT_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return subject, 'keyword'
    return 'General Medicine', 'needs_llm'


# ---------------------------------------------------------------------------
# Confidence scoring
# ---------------------------------------------------------------------------

def assign_confidence(q: dict) -> tuple:
    """Returns (confidence_level, review_reason)."""
    q_text  = q.get('question', '')
    opts    = q.get('options', {})
    correct = q.get('correctAnswer', '')
    explanation     = q.get('explanation', '')
    subject_source  = q.get('_subject_source', 'keyword')

    # Low: structural problems
    if not q_text or len(q_text.strip()) < 5:
        return 'low', 'Question text missing or too short'
    if not correct or correct not in ('A', 'B', 'C', 'D'):
        return 'low', f'Correct answer missing or invalid: {repr(correct)}'
    missing_opts = [k for k in ('A', 'B', 'C', 'D') if len(opts.get(k, '').strip()) < 5]
    if missing_opts:
        return 'low', f'Options missing or too short: {missing_opts}'

    # Medium: complete but uncertain
    reasons = []
    if not explanation:
        reasons.append('explanation absent')
    if subject_source == 'needs_llm':
        reasons.append('subject needed LLM classification')
    if reasons:
        return 'medium', '; '.join(reasons)

    return 'high', ''


# ---------------------------------------------------------------------------
# Format detection via page 0 sample
# ---------------------------------------------------------------------------

def extract_page_sample(pdf_path: str, page_num: int = 0) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        if page_num < len(pdf.pages):
            return pdf.pages[page_num].extract_text() or ""
    return ""


# Three patterns from spec — used for pattern-match counting to aid detection
_PAT_A = re.compile(
    r'(\d+)\.\s+(.+?)\n\s*[Aa]\.\s+(.+?)\n\s*[Bb]\.\s+(.+?)\n\s*[Cc]\.\s+(.+?)\n\s*[Dd]\.\s+(.+?)\n',
    re.DOTALL,
)
_PAT_B = re.compile(
    r'Q\.?\s*(\d+)[.)]\s*(.+?)\n\s*\(?[Aa]\)?\s*(.+?)\n\s*\(?[Bb]\)?\s*(.+?)\n\s*\(?[Cc]\)?\s*(.+?)\n\s*\(?[Dd]\)?\s*(.+?)\n',
    re.DOTALL,
)
_PAT_C = re.compile(
    r'(\d+)\)\s*(.+?)\n\s*1\)\s*(.+?)\n\s*2\)\s*(.+?)\n\s*3\)\s*(.+?)\n\s*4\)\s*(.+?)\n',
    re.DOTALL,
)


def detect_format(sample: str) -> str:
    """Return format code 'A'/'B'/'C'/'D' based on hard markers then pattern counts."""
    # Hard structural markers (highest confidence)
    if 'Ques No:' in sample or ('O1:' in sample and 'O2:' in sample):
        return 'C'  # 2022-2023
    if re.search(r'Ques\s+\d+\.', sample):
        return 'D'  # 2024
    if re.search(r'Question\s+\d+', sample) and (
        'A>' in sample or re.search(r'Answer\s*[-–]', sample)
    ):
        return 'B'  # 2017

    # Pattern-count fallback on raw sample text
    counts = [len(_PAT_A.findall(sample)), len(_PAT_B.findall(sample)), len(_PAT_C.findall(sample))]
    best = counts.index(max(counts))
    if max(counts) > 0:
        return ['A', 'B', 'C'][best]

    # Soft markers
    if 'Correct Answer' in sample:
        return 'A'

    return 'A'  # default


# ---------------------------------------------------------------------------
# Format-specific extractors
# ---------------------------------------------------------------------------

def extract_format_a(pdf_path: str, year: int, shift: int = 1) -> list:
    """2012-2016, 2018-2020: one question per page, a) options, 'Correct Answer - X'."""
    questions = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            raw = page.extract_text()
            if not raw:
                continue
            text = clean_text(raw)

            m = re.match(r'^(\d+)[.)]\s+(.+)', text, re.DOTALL)
            if not m:
                continue

            q_num = int(m.group(1))
            rest  = m.group(2)

            opt_pattern = r'([a-dA-D])[)\.]\s*(.+?)(?=[a-dA-D][)\.]|Correct Answer|$)'
            opts_raw = re.findall(opt_pattern, rest, re.DOTALL | re.IGNORECASE)
            if len(opts_raw) < 2:
                continue

            first_opt = re.search(r'[a-dA-D][)\.]\s', rest, re.IGNORECASE)
            q_text = rest[:first_opt.start()].strip() if first_opt else ''

            options = {}
            for letter, opt_text in opts_raw:
                key = letter.upper()
                options[key] = re.split(r'Correct Answer', opt_text, flags=re.IGNORECASE)[0].strip()

            ans_match = re.search(r'Correct Answer\s*[-–]\s*([A-Da-d])', text, re.IGNORECASE)
            correct = ans_match.group(1).upper() if ans_match else ''

            exp_match = re.search(
                r'(?:Ans\.|Answer\.?)\s+(?:is\s+)?[\'"]?[a-dA-D][\'"]?[,.]?\s+(?:i\.e\.,?\s*)?(.+)',
                text, re.DOTALL | re.IGNORECASE,
            )
            explanation = exp_match.group(1).strip()[:1000] if exp_match else ''

            subj, src = infer_subject_keyword(q_text)
            questions.append({
                'id': make_question_id(year, shift, q_num),
                'year': year, 'shift': shift, 'questionNumber': q_num,
                'question': q_text,
                'options': {k: options.get(k, '') for k in ('A', 'B', 'C', 'D')},
                'correctAnswer': correct,
                'explanation': explanation,
                'subject': subj, '_subject_source': src,
                'topic': '',
                'difficulty': infer_difficulty(q_text, options),
                'tags': [],
            })
    return questions


def extract_format_b(pdf_path: str, year: int, shift: int = 1) -> list:
    """2017: 'Question N', 'A> option', 'Answer - X'."""
    questions = []
    full_text = ''
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            raw = page.extract_text()
            if raw:
                full_text += '\n' + raw
    full_text = clean_text(full_text)

    parts = re.split(r'Question\s+(\d+)', full_text)
    i = 1
    while i < len(parts) - 1:
        q_num = int(parts[i])
        body  = parts[i + 1]
        i += 2

        opts_raw = re.findall(r'([A-D])>\s*(.+?)(?=[A-D]>|Answer\s*[-–]|$)', body, re.DOTALL)
        if len(opts_raw) < 2:
            continue

        first_opt = re.search(r'[A-D]>', body)
        q_text = body[:first_opt.start()].strip() if first_opt else ''

        options = {}
        for letter, opt_text in opts_raw:
            options[letter] = re.split(r'Answer\s*[-–]', opt_text, flags=re.IGNORECASE)[0].strip()

        ans_match = re.search(r'Answer\s*[-–]\s*([A-Da-d])', body, re.IGNORECASE)
        correct = ans_match.group(1).upper() if ans_match else ''

        exp_match = re.search(r'Explanation\s*[-–]\s*(.+)', body, re.DOTALL | re.IGNORECASE)
        explanation = exp_match.group(1).strip()[:1000] if exp_match else ''

        subj, src = infer_subject_keyword(q_text)
        questions.append({
            'id': make_question_id(year, shift, q_num),
            'year': year, 'shift': shift, 'questionNumber': q_num,
            'question': q_text,
            'options': {k: options.get(k, '') for k in ('A', 'B', 'C', 'D')},
            'correctAnswer': correct,
            'explanation': explanation,
            'subject': subj, '_subject_source': src,
            'topic': '',
            'difficulty': infer_difficulty(q_text, options),
            'tags': [],
        })
    return questions


def extract_format_c(pdf_path: str, year: int, shift: int = 1) -> list:
    """2022-2023: 'Ques No: N', 'O1:', 'Ans: N'."""
    questions = []
    full_text = ''
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            raw = page.extract_text()
            if raw:
                full_text += '\n' + raw

    parts = re.split(r'Ques No:\s*(\d+)', full_text)
    i = 1
    while i < len(parts) - 1:
        q_num = int(parts[i])
        body  = parts[i + 1]
        i += 2

        subj_match  = re.search(r'Subject:\s*(.+?)(?:Topic:|Sub-Topic:|O1:|$)',  body, re.DOTALL | re.IGNORECASE)
        topic_match = re.search(r'Topic:\s*(.+?)(?:Sub-Topic:|O1:|$)',            body, re.DOTALL | re.IGNORECASE)
        subject_raw = clean_text(subj_match.group(1))  if subj_match  else ''
        topic_raw   = clean_text(topic_match.group(1)) if topic_match else ''

        q_match = re.search(r'Sub-Topic:.*?\n(.*?)(?:O1:|$)', body, re.DOTALL | re.IGNORECASE)
        if not q_match:
            q_match = re.search(r'Topic:.*?\n(.*?)(?:O1:|$)', body, re.DOTALL | re.IGNORECASE)
        q_text = clean_text(q_match.group(1)) if q_match else ''

        opt_texts = re.findall(r'O[1-4]:\s*\n?(.*?)(?=O[1-4]:|Ans:|$)', body, re.DOTALL | re.IGNORECASE)
        if len(opt_texts) < 2:
            continue

        options = {['A', 'B', 'C', 'D'][idx]: clean_text(opt) for idx, opt in enumerate(opt_texts[:4])}

        ans_match = re.search(r'Ans:\s*(\d)', body, re.IGNORECASE)
        correct = map_answer_letter(ans_match.group(1), 'numbered') if ans_match else ''

        if subject_raw:
            subj, src = subject_raw, 'keyword'
        else:
            subj, src = infer_subject_keyword(q_text)

        questions.append({
            'id': make_question_id(year, shift, q_num),
            'year': year, 'shift': shift, 'questionNumber': q_num,
            'question': q_text,
            'options': {k: options.get(k, '') for k in ('A', 'B', 'C', 'D')},
            'correctAnswer': correct,
            'explanation': '',
            'subject': subj, '_subject_source': src,
            'topic': topic_raw,
            'difficulty': infer_difficulty(q_text, options),
            'tags': [],
        })
    return questions


def extract_format_d(pdf_path: str, year: int, shift: int = 1) -> list:
    """2024 shift 1 & 2: 'Ques N.', 'A. option', 'Ans. X'."""
    questions = []
    full_text = ''
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            raw = page.extract_text()
            if raw:
                full_text += '\n' + raw
    full_text = clean_text(full_text)

    parts = re.split(r'Ques\s+(\d+)\.', full_text)
    i = 1
    while i < len(parts) - 1:
        q_num = int(parts[i])
        body  = parts[i + 1]
        i += 2

        opts_raw = re.findall(r'([A-Da-d])\.\s+(.+?)(?=[A-Da-d]\.\s|Ans\.|$)', body, re.DOTALL)
        if len(opts_raw) < 2:
            continue

        first_opt = re.search(r'[A-Da-d]\.\s', body)
        q_text = body[:first_opt.start()].strip() if first_opt else ''

        options = {}
        for letter, opt_text in opts_raw:
            key = letter.upper()
            options[key] = re.split(r'Ans\.', opt_text, flags=re.IGNORECASE)[0].strip()

        ans_match = re.search(r'Ans\.\s*([A-Da-d])', body, re.IGNORECASE)
        correct = ans_match.group(1).upper() if ans_match else ''

        subj, src = infer_subject_keyword(q_text)
        questions.append({
            'id': make_question_id(year, shift, q_num),
            'year': year, 'shift': shift, 'questionNumber': q_num,
            'question': q_text,
            'options': {k: options.get(k, '') for k in ('A', 'B', 'C', 'D')},
            'correctAnswer': correct,
            'explanation': '',
            'subject': subj, '_subject_source': src,
            'topic': '',
            'difficulty': infer_difficulty(q_text, options),
            'tags': [],
        })
    return questions


EXTRACTORS = {'A': extract_format_a, 'B': extract_format_b, 'C': extract_format_c, 'D': extract_format_d}


# ---------------------------------------------------------------------------
# Timeout wrapper (Unix / macOS only)
# ---------------------------------------------------------------------------

class _Timeout(Exception):
    pass


def _alarm_handler(signum, frame):
    raise _Timeout()


def extract_with_timeout(fn, pdf_path: str, year: int, shift: int, timeout_sec: int = 180) -> list:
    old = signal.signal(signal.SIGALRM, _alarm_handler)
    signal.alarm(timeout_sec)
    try:
        return fn(pdf_path, year, shift)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


# ---------------------------------------------------------------------------
# LLM subject classification (batched, 20 at a time)
# ---------------------------------------------------------------------------

SUBJECT_LIST = (
    'Anatomy, Physiology, Biochemistry, Pharmacology, Pathology, Microbiology, '
    'Forensic Medicine, Preventive & Social Medicine, General Medicine, Surgery, '
    'Obstetrics & Gynaecology, Paediatrics, Orthopaedics, Ophthalmology, ENT, '
    'Dermatology, Psychiatry, Radiology, Anaesthesia, Community Medicine'
)


def classify_subjects_llm(questions: list) -> list:
    """Classify subjects for questions where keyword matching defaulted to General Medicine."""
    if not ANTHROPIC_API_KEY:
        return questions

    try:
        import anthropic as ant
    except ImportError:
        print('  [LLM] anthropic package not installed, skipping LLM classification')
        return questions

    needs = [(i, q) for i, q in enumerate(questions) if q.get('_subject_source') == 'needs_llm']
    if not needs:
        return questions

    print(f'  [LLM] Classifying {len(needs)} questions in batches of 20...')
    client = ant.Anthropic(api_key=ANTHROPIC_API_KEY)

    for batch_start in range(0, len(needs), 20):
        batch = needs[batch_start: batch_start + 20]
        prompt = (
            f'For each NEET PG question below, return only the medical subject from this list: '
            f'[{SUBJECT_LIST}]. Return a JSON array of subjects in the same order.\n\n'
        )
        for j, (_, q) in enumerate(batch):
            prompt += f'{j + 1}. {q["question"][:200]}\n'

        try:
            response = client.messages.create(
                model='claude-haiku-4-5-20251001',
                max_tokens=512,
                messages=[{'role': 'user', 'content': prompt}],
            )
            text = response.content[0].text
            arr_m = re.search(r'\[.*?\]', text, re.DOTALL)
            if arr_m:
                subjects = json.loads(arr_m.group())
                for j, (idx, _) in enumerate(batch):
                    if j < len(subjects):
                        questions[idx]['subject'] = str(subjects[j])
                        # Keep _subject_source as 'needs_llm' so confidence stays medium
        except Exception as exc:
            print(f'  [LLM] Batch {batch_start // 20 + 1} failed: {exc}')

    return questions


# ---------------------------------------------------------------------------
# PDF config
# ---------------------------------------------------------------------------

PDF_CONFIG = [
    ('data/pdfs/*2012*.pdf',         2012, 1),
    ('data/pdfs/*2013*.pdf',         2013, 1),
    ('data/pdfs/*2014*.pdf',         2014, 1),
    ('data/pdfs/*2015*.pdf',         2015, 1),
    ('data/pdfs/*2016*.pdf',         2016, 1),
    ('data/pdfs/*2017*.pdf',         2017, 1),
    ('data/pdfs/*2018*.pdf',         2018, 1),
    ('data/pdfs/*2019*.pdf',         2019, 1),
    ('data/pdfs/*2020*.pdf',         2020, 1),
    # 2021 is image-based (scanned) — no text layer, skip
    ('data/pdfs/*2022*.pdf',         2022, 1),
    ('data/pdfs/*2023*.pdf',         2023, 1),
    ('data/pdfs/*2024*shift-1*.pdf', 2024, 1),
    ('data/pdfs/*2024*shift-2*.pdf', 2024, 2),
]

SKIP_YEARS = {2021}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_extraction():
    all_main:   list = []   # high + medium
    all_review: list = []   # low

    report = {
        'totalExtracted': 0,
        'totalMain': 0,
        'totalReview': 0,
        'byConfidence': {'high': 0, 'medium': 0, 'low': 0},
        'byYear': {},
        'bySubject': {},
        'skipped': ['2021: Image-based PDF (scanned), no text extraction possible. Requires OCR.'],
        'issues': [],
    }

    for pattern, year, shift in PDF_CONFIG:
        if year in SKIP_YEARS:
            continue

        files = sorted(glob.glob(pattern))
        if not files:
            msg = f'{year}: No file matched pattern {pattern}'
            report['skipped'].append(msg)
            print(f'  SKIP: {msg}')
            continue

        for pdf_path in files:
            print(f'\nProcessing {year} PDF...')

            # ---- Step 1: format detection ----
            try:
                sample = extract_page_sample(pdf_path)
                fmt = detect_format(sample)
            except Exception as exc:
                fmt = 'A'
                print(f'  Format detection failed ({exc}), defaulting to A')

            # ---- Step 2: primary extraction ----
            try:
                qs = extract_with_timeout(EXTRACTORS[fmt], pdf_path, year, shift)
            except _Timeout:
                print(f'  Extraction timed out for format {fmt}')
                qs = []
            except Exception as exc:
                print(f'  Extractor {fmt} error: {exc}')
                qs = []

            # ---- Step 3: try all extractors if result is poor ----
            if len(qs) < 50:
                print(f'  Only {len(qs)} questions from format {fmt} — trying other extractors...')
                for alt_fmt, alt_fn in EXTRACTORS.items():
                    if alt_fmt == fmt:
                        continue
                    try:
                        alt_qs = extract_with_timeout(alt_fn, pdf_path, year, shift)
                        if len(alt_qs) > len(qs):
                            print(f'  Format {alt_fmt} gives {len(alt_qs)} questions (switching)')
                            qs = alt_qs
                            fmt = alt_fmt
                    except Exception:
                        pass

            # ---- Step 4: LLM subject classification ----
            qs = classify_subjects_llm(qs)

            # ---- Step 5: assign confidence and split ----
            year_stats = {'total': 0, 'high': 0, 'medium': 0, 'low': 0}
            for q in qs:
                conf, reason = assign_confidence(q)
                q['confidence'] = conf
                q.pop('_subject_source', None)   # remove internal field from output

                year_stats['total'] += 1
                year_stats[conf]    += 1
                report['bySubject'][q.get('subject', 'Unknown')] = (
                    report['bySubject'].get(q.get('subject', 'Unknown'), 0) + 1
                )

                if conf == 'low':
                    q['review_reason'] = reason
                    all_review.append(q)
                else:
                    all_main.append(q)

            year_key = f'{year}-shift{shift}'
            report['byYear'][year_key] = year_stats

            print(
                f'Processing {year} PDF... extracted {year_stats["total"]} questions '
                f'({year_stats["high"]} high, {year_stats["medium"]} medium, {year_stats["low"]} low)'
            )

            if year_stats['total'] == 0:
                report['issues'].append(f'{year_key}: 0 questions extracted — check PDF format')

    # ---- Final report ----
    report['totalExtracted'] = sum(y['total']  for y in report['byYear'].values())
    report['totalMain']      = len(all_main)
    report['totalReview']    = len(all_review)
    for lvl in ('high', 'medium', 'low'):
        report['byConfidence'][lvl] = sum(y[lvl] for y in report['byYear'].values())

    with open(MAIN_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(all_main, f, indent=2, ensure_ascii=False)
    print(f'\nWrote {len(all_main)} questions  →  {MAIN_OUTPUT}')

    with open(REVIEW_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(all_review, f, indent=2, ensure_ascii=False)
    print(f'Wrote {len(all_review)} questions  →  {REVIEW_OUTPUT}')

    with open(REPORT_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f'Wrote report              →  {REPORT_OUTPUT}')

    print('\n=== Final Stats ===')
    print(f'Total extracted : {report["totalExtracted"]}')
    print(f'  High          : {report["byConfidence"]["high"]}')
    print(f'  Medium        : {report["byConfidence"]["medium"]}')
    print(f'  Low (review)  : {report["byConfidence"]["low"]}')
    print(f'Main output     : {len(all_main)} questions')
    print(f'Review queue    : {len(all_review)} questions')
    print('\nBy year:')
    for k, v in report['byYear'].items():
        print(f'  {k}: {v["total"]} total  ({v["high"]} H / {v["medium"]} M / {v["low"]} L)')


if __name__ == '__main__':
    run_extraction()
