"""
NEET PG PDF Question Extractor - High-Accuracy Version
Uses word-level position filtering to remove watermarks precisely.

Handles 5 PDF formats:
  Format A: 2012-2016, 2018-2020 - "N. Question\na) Opt\nCorrect Answer - X\nAns. explanation"
  Format B: 2017 - "Question N\nA> Opt\nAnswer - X\nExplanation - text"
  Format C: 2022-2023 - "Ques No: N\nSubject: X\nTopic: Y\nO1:\nO2:\nAns: N"
  Format D: 2024 Shift 1 - "Ques N. Question\nA. Opt\nAns. X"
  Format E: 2024 Shift 2 - same but lowercase options a. b. c. d.
"""

import re
import json
import pdfplumber
import glob
import os
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# Watermark-aware text extraction
# ─────────────────────────────────────────────────────────────────────────────

WATERMARK_PATTERN = re.compile(
    r'^(www\.?|First|Ranker|\.com|wwwA\.|FnirasttRoanmkery|srasltivRaaryn|gklearn|wmwin)',
    re.IGNORECASE
)

# Exact characters that appear in "www.FirstRanker.com" (case-sensitive)
# Includes both uppercase F (from "First") and uppercase R (from "Ranker")
# Answer letters A, B, C, D are NOT in this set → they will never be filtered
_WM_CHARS = frozenset('wfirstRankecomF.')

def is_watermark_word(word: dict, page_width: float) -> bool:
    text = word['text']
    x0 = word['x0']
    # Exact watermark URL matches
    if WATERMARK_PATTERN.match(text) or 'FirstRanker' in text:
        return True
    if len(text) == 1:
        # 'w' only ever appears alone as watermark — filter regardless of x
        # (content never has a lone 'w' in medical MCQ text)
        if text == 'w' and x0 > 50:
            return True
        # Other watermark chars at x > 190 (diagonal watermark position)
        if x0 > 190 and text in _WM_CHARS:
            return True
    return False


def clean_option(text: str) -> str:
    """Strip leading/trailing stray watermark chars from option/question text."""
    # Remove lone watermark chars at start or end of string
    text = re.sub(r'^[wFfRr]\s+', '', text)
    text = re.sub(r'\s+[wFfRr]$', '', text)
    return text.strip()


def extract_page_text(page) -> str:
    """
    Extract clean text from a PDF page using word-level position filtering.
    Returns reconstructed text with proper line breaks.
    """
    page_width = page.width
    page_height = page.height

    # Use tight y_tolerance=2 to prevent watermark chars from merging
    # with content words on adjacent lines
    try:
        words = page.extract_words(y_tolerance=2, x_tolerance=3)
    except Exception:
        return ""

    if not words:
        return ""

    # Filter watermarks
    clean_words = []
    for w in words:
        if is_watermark_word(w, page_width):
            continue
        # Also skip words in top/bottom border zone (y < 45 or y > height-30)
        # that appear at x > 180 — those are header/footer watermarks
        if (w['top'] < 45 or w['top'] > page_height - 30) and w['x0'] > 180:
            continue
        clean_words.append(w)

    if not clean_words:
        return ""

    # Group words into lines by y coordinate (tolerance=4)
    lines = []
    current_line = [clean_words[0]]
    for w in clean_words[1:]:
        if abs(w['top'] - current_line[-1]['top']) <= 4:
            current_line.append(w)
        else:
            lines.append(current_line)
            current_line = [w]
    lines.append(current_line)

    # Sort each line by x position and join
    text_lines = []
    for line_words in lines:
        line_words.sort(key=lambda w: w['x0'])
        text_lines.append(' '.join(w['text'] for w in line_words))

    return '\n'.join(text_lines)


def get_pdf_text(pdf_path: str) -> str:
    """Extract full clean text from all pages of a PDF."""
    parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = extract_page_text(page)
            if text:
                parts.append(text)
    return '\n'.join(parts)


def get_pdf_pages(pdf_path: str) -> list:
    """Return list of clean text strings, one per page."""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = extract_page_text(page)
            pages.append(text)
    return pages


# ─────────────────────────────────────────────────────────────────────────────
# Subject inference
# ─────────────────────────────────────────────────────────────────────────────

SUBJECT_KEYWORDS = {
    'Anatomy': ['anatomy', 'anatomical', 'histology', 'embryology', 'nerve', 'artery', 'vein',
                'muscle', 'bone', 'vertebra', 'intertubercular', 'thorax', 'pelvis', 'limb',
                'humerus', 'femur', 'cranial', 'ligament', 'tendon', 'cartilage'],
    'Physiology': ['physiology', 'physiological', 'receptor', 'hormone', 'cardiac output',
                   'renal', 'respiratory', 'membrane potential', 'action potential', 'reflex',
                   'hemoglobin', 'blood pressure', 'erythrocyte'],
    'Biochemistry': ['biochemistry', 'enzyme', 'metabolism', 'glucose', 'protein', 'dna', 'rna',
                     'vitamin', 'amino acid', 'fatty acid', 'glycolysis', 'krebs', 'nucleotide',
                     'coenzyme', 'substrate', 'catalyst'],
    'Pathology': ['pathology', 'neoplasm', 'carcinoma', 'tumour', 'tumor', 'biopsy',
                  'histopathology', 'granuloma', 'infarction', 'necrosis', 'hyperplasia',
                  'metaplasia', 'dysplasia', 'malignant', 'benign', 'fibrosis', 'abscess'],
    'Pharmacology': ['pharmacology', 'drug', 'pharmacokinetics', 'receptor agonist', 'antagonist',
                     'dose', 'toxicity', 'antibiotic', 'antifungal', 'antiviral', 'half-life',
                     'bioavailability', 'mechanism of action'],
    'Microbiology': ['microbiology', 'bacteria', 'virus', 'fungus', 'parasite', 'culture',
                     'stain', 'gram positive', 'gram negative', 'organism', 'infection', 'pathogen',
                     'staphylococcus', 'streptococcus', 'mycobacterium', 'plasmodium', 'entamoeba'],
    'Medicine': ['medicine', 'hypertension', 'diabetes', 'thyroid', 'cardiac', 'pulmonary',
                 'renal failure', 'anemia', 'lupus', 'rheumatoid', 'hepatitis', 'cirrhosis',
                 'myocardial', 'pneumonia', 'fever', 'jaundice', 'ascites', 'atrial fibrillation'],
    'Surgery': ['surgery', 'surgical', 'appendix', 'hernia', 'laparoscopy', 'anastomosis',
                'bowel', 'colostomy', 'ileostomy', 'cholecystectomy', 'incision', 'excision',
                'resection', 'amputation', 'mastectomy', 'thyroidectomy'],
    'Obstetrics & Gynaecology': ['obstetric', 'gynaecology', 'gynecology', 'pregnancy', 'labour',
                                  'cervix', 'uterus', 'ovary', 'fetus', 'placenta', 'amenorrhea',
                                  'menstrual', 'gestational', 'antepartum', 'postpartum', 'eclampsia'],
    'Paediatrics': ['paediatric', 'pediatric', 'child', 'infant', 'neonatal', 'developmental',
                    'milestones', 'vaccination', 'immunization schedule', 'growth'],
    'Psychiatry': ['psychiatry', 'psychiatric', 'schizophrenia', 'depression', 'anxiety',
                   'bipolar', 'cognitive', 'psychosis', 'delusion', 'hallucination', 'ocd'],
    'Radiology': ['radiology', 'x-ray', 'ct scan', 'mri', 'ultrasound', 'imaging', 'radiograph',
                  'contrast', 'opacity', 'calcification'],
    'Orthopaedics': ['orthopaedic', 'orthopedic', 'fracture', 'dislocation', 'joint replacement',
                     'osteomyelitis', 'osteoporosis', 'scoliosis', 'arthritis'],
    'ENT': ['ent', 'ear', 'nose', 'throat', 'larynx', 'pharynx', 'tonsil', 'otitis', 'rhinitis',
            'sinusitis', 'deafness', 'vertigo', 'epistaxis'],
    'Ophthalmology': ['ophthalmology', 'eye', 'retina', 'glaucoma', 'cataract', 'cornea',
                      'conjunctiva', 'iris', 'intraocular pressure', 'vision'],
    'Dermatology': ['dermatology', 'skin', 'rash', 'psoriasis', 'eczema', 'melanoma',
                    'acne', 'vitiligo', 'pemphigus', 'urticaria', 'leprosy'],
    'Anaesthesia': ['anaesthesia', 'anesthesia', 'sedation', 'intubation', 'spinal block',
                    'epidural', 'ventilator', 'airway', 'analgesic'],
    'Forensic Medicine': ['forensic', 'medicolegal', 'autopsy', 'rigor mortis', 'postmortem',
                          'cadaver', 'cause of death', 'injuries', 'exhumation'],
    'Community Medicine': ['community medicine', 'epidemiology', 'public health', 'vaccination',
                           'prevalence', 'incidence', 'sensitivity', 'specificity', 'odds ratio',
                           'relative risk', 'surveillance', 'screening'],
}


def infer_subject(text: str) -> str:
    text_lower = text.lower()
    best_subject = 'General Medicine'
    best_count = 0
    for subject, keywords in SUBJECT_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in text_lower)
        if count > best_count:
            best_count = count
            best_subject = subject
    return best_subject


def infer_difficulty(question: str, options: dict) -> str:
    total_len = len(question) + sum(len(v) for v in options.values())
    if total_len < 200:
        return 'Easy'
    elif total_len < 400:
        return 'Medium'
    return 'Hard'


def make_id(year: int, shift: int, q_num: int) -> str:
    return f"neetpg-{year}-s{shift}-q{q_num:04d}"


def normalize_answer(ans: str, style: str = 'letter') -> str:
    """Convert answer to A/B/C/D."""
    ans = ans.strip().upper()
    if style == 'numbered':
        return {'1': 'A', '2': 'B', '3': 'C', '4': 'D'}.get(ans, ans)
    if style == 'letter':
        return ans if ans in 'ABCD' else ''
    return ans


def _extract_answer_format_a(text: str) -> str:
    """
    Extract correct answer letter from various answer patterns used in 2012-2020 PDFs.
    Returns uppercase A/B/C/D or empty string.
    """
    patterns = [
        # "Correct Answer - B" or "Correct Answer – B"
        r'Correct Answer\s*[-–]\s*([A-D])',
        # "Correct Answer\nAnswer -C. text" or "Answer - C"
        r'Answer\s*[-–]\s*([A-D])[.):\s]',
        # "Answer A. text" or "Answer B:"
        r'Answer\s+([A-D])[.):\s]',
        # "Ans: B." or "Ans. B" or "Ans: B"
        r'Ans[.:\s]+([A-D])[.):\s]',
        # "Ans. is 'b' i.e.," — letter in quotes
        r"Ans[.:\s]+is\s+['\"]([a-d])['\"]",
        # "Correct Answer - b" lowercase
        r'Correct Answer\s*[-–]\s*([a-d])',
        r'Answer\s*[-–]\s*([a-d])[.):\s]',
        r'Answer\s+([a-d])[.):\s]',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).upper()
    return ''


# ─────────────────────────────────────────────────────────────────────────────
# FORMAT A: 2012-2016, 2018-2020
# Each question on its own page (1 page per question).
# Pattern: "N. Question text\na) Opt\nb) Opt\nc) Opt\nd) Opt\nCorrect Answer - X\nAns. explanation"
# ─────────────────────────────────────────────────────────────────────────────

def extract_format_a(pdf_path: str, year: int, shift: int = 1) -> list:
    """One question per page format. Parses each page independently."""
    questions = []
    seen_nums = set()

    pages = get_pdf_pages(pdf_path)

    for page_text in pages:
        if not page_text:
            continue

        # Skip stray single watermark chars as standalone lines
        lines = [l.strip() for l in page_text.split('\n')
                 if l.strip() and not (len(l.strip()) == 1 and l.strip() in _WM_CHARS)]
        if not lines:
            continue

        # First meaningful line should be "N. Question text"
        # Might be split across first 2 lines if question number wraps
        first_line = lines[0]
        q_match = re.match(r'^(\d+)[.)]\s+(.*)', first_line)
        if not q_match:
            continue

        q_num = int(q_match.group(1))
        # Avoid duplicates (some PDFs repeat question numbers across sections)
        if q_num in seen_nums:
            continue

        # Collect question text lines until we hit the first option
        q_text_lines = [q_match.group(2).strip()]
        i = 1

        # Option pattern: a) or a. at start of line
        opt_line_re = re.compile(r'^([a-dA-D])[).]\s+(.*)', re.IGNORECASE)

        while i < len(lines) and not opt_line_re.match(lines[i]):
            if not lines[i].startswith('Correct Answer') and lines[i]:
                q_text_lines.append(lines[i])
            i += 1

        q_text = ' '.join(q_text_lines).strip()

        # Parse options
        options = {}
        while i < len(lines):
            line = lines[i]
            om = opt_line_re.match(line)
            if not om:
                break
            key = om.group(1).upper()
            opt_text = om.group(2).strip()
            i += 1
            # Continuation lines for this option (before next option letter)
            while i < len(lines) and not opt_line_re.match(lines[i]) and not lines[i].startswith('Correct Answer'):
                opt_text += ' ' + lines[i].strip()
                i += 1
            options[key] = opt_text.strip()

        if len(options) < 2:
            continue

        # Find correct answer — handle multiple patterns across all years
        correct = _extract_answer_format_a(page_text)
        if not correct:
            continue

        # Find explanation
        exp_match = re.search(
            r'(?:Ans[.:]|Answer[.:]?)\s+(?:is\s+)?[\'"]?[a-dA-D][\'"]?[,.]?\s+(?:i\.e[.,]?\s*)?(.+)',
            page_text, re.DOTALL | re.IGNORECASE
        )
        explanation = exp_match.group(1).strip()[:1000] if exp_match else ""
        explanation = re.sub(r'\s{2,}', ' ', explanation).strip()

        if not q_text:
            continue

        seen_nums.add(q_num)
        questions.append({
            "id": make_id(year, shift, q_num),
            "year": year,
            "shift": shift,
            "questionNumber": q_num,
            "question": q_text,
            "options": {k: options.get(k, '') for k in ['A', 'B', 'C', 'D']},
            "correctAnswer": correct,
            "explanation": explanation,
            "subject": infer_subject(q_text),
            "topic": "",
            "difficulty": infer_difficulty(q_text, options),
            "tags": [],
        })

    return questions


# ─────────────────────────────────────────────────────────────────────────────
# FORMAT B: 2017
# "Question N\nQuestion text\nA> Opt\nB> Opt\nC> Opt\nD> Opt\nAnswer - X\nExplanation - text"
# ─────────────────────────────────────────────────────────────────────────────

def extract_format_b(pdf_path: str, year: int, shift: int = 1) -> list:
    """2017 format: Question N with A> B> C> D> options (also handles A. format)."""
    questions = []

    full_text = get_pdf_text(pdf_path)
    lines = [l.strip() for l in full_text.split('\n') if l.strip()]

    # Find "Question N" markers — text may start on the same line as the number
    q_starts = []
    for i, line in enumerate(lines):
        m = re.match(r'^Question\s+(\d+)\s*(.*)', line, re.IGNORECASE)
        if m:
            q_starts.append((i, int(m.group(1)), m.group(2).strip()))

    # Option patterns: "A> text" OR "A. text" OR "A) text"
    opt_re = re.compile(r'^([A-D])[>.)]\s*(.*)', re.IGNORECASE)
    # Answer patterns: "Answer - C", "Answer: C", "Answer: Option C", "Answer C."
    ans_re = re.compile(
        r'Answer[:\s]*(?:Option\s+)?[-–]?\s*([A-Da-d])\b',
        re.IGNORECASE
    )
    exp_re = re.compile(r'^Explanation\s*[-–:]\s*(.*)', re.IGNORECASE)

    for idx, (start_line, q_num, inline_text) in enumerate(q_starts):
        end_line = q_starts[idx + 1][0] if idx + 1 < len(q_starts) else len(lines)
        block = lines[start_line + 1:end_line]

        q_text_lines = [inline_text] if inline_text else []
        options = {}
        correct = ''
        explanation_lines = []
        state = 'question'
        current_opt = None

        for line in block:
            # Skip stray single watermark chars that escaped filtering
            if len(line) == 1 and line in 'wWfFiIrRsStTaAnNkKeEcCoOmM.':
                continue

            exp_m = exp_re.match(line)
            if exp_m:
                state = 'explanation'
                if exp_m.group(1):
                    explanation_lines.append(exp_m.group(1))
                continue

            ans_m = ans_re.match(line)
            if ans_m and not opt_re.match(line):  # don't confuse "Answer" with option
                if not correct:  # take first match only
                    correct = ans_m.group(1).upper()
                state = 'answer'
                continue

            opt_m = opt_re.match(line)
            if opt_m:
                state = 'option'
                current_opt = opt_m.group(1).upper()
                options[current_opt] = opt_m.group(2).strip()
                continue

            if state == 'question':
                q_text_lines.append(line)
            elif state == 'option' and current_opt:
                options[current_opt] += ' ' + line
            elif state == 'explanation':
                explanation_lines.append(line)

        q_text = ' '.join(q_text_lines).strip()
        # Remove stray watermark single-char prefix
        q_text = re.sub(r'^[wWfFrR]\s+', '', q_text)
        explanation = ' '.join(explanation_lines).strip()[:1000]

        if not q_text or not correct or len(options) < 2:
            continue

        questions.append({
            "id": make_id(year, shift, q_num),
            "year": year,
            "shift": shift,
            "questionNumber": q_num,
            "question": q_text,
            "options": {k: options.get(k, '') for k in ['A', 'B', 'C', 'D']},
            "correctAnswer": correct,
            "explanation": explanation,
            "subject": infer_subject(q_text),
            "topic": "",
            "difficulty": infer_difficulty(q_text, options),
            "tags": [],
        })

    return questions


# ─────────────────────────────────────────────────────────────────────────────
# FORMAT C: 2022-2023
# "Ques No: N\nSubject: X\nTopic: Y\nSub-Topic:\nQuestion text\nO1:\nOpt\nO2:\nOpt\nAns: N"
# ─────────────────────────────────────────────────────────────────────────────

def extract_format_c(pdf_path: str, year: int, shift: int = 1) -> list:
    """2022/2023 format with Subject/Topic metadata and O1-O4 options."""
    questions = []

    full_text = get_pdf_text(pdf_path)
    # Filter stray single watermark chars from lines
    lines = [l.strip() for l in full_text.split('\n')
             if l.strip() and not (len(l.strip()) == 1 and l.strip() in _WM_CHARS)]

    # Find "Ques No: N" markers
    q_starts = []
    for i, line in enumerate(lines):
        m = re.match(r'^Ques\s*No\s*:\s*(\d+)$', line, re.IGNORECASE)
        if m:
            q_starts.append((i, int(m.group(1))))

    for idx, (start_line, q_num) in enumerate(q_starts):
        end_line = q_starts[idx + 1][0] if idx + 1 < len(q_starts) else len(lines)
        block = lines[start_line + 1:end_line]

        subject = ''
        topic = ''
        q_text_lines = []
        current_opt_key = None
        options = {}
        correct = ''
        state = 'meta'  # meta → question → option → answer

        for line in block:
            subj_m = re.match(r'^Subject:\s*(.*)', line, re.IGNORECASE)
            topic_m = re.match(r'^Topic:\s*(.*)', line, re.IGNORECASE)
            subtopic_m = re.match(r'^Sub-Topic:\s*(.*)', line, re.IGNORECASE)
            opt_m = re.match(r'^O([1-4]):\s*(.*)', line, re.IGNORECASE)
            ans_m = re.match(r'^Ans:\s*(\d)', line, re.IGNORECASE)

            if subj_m:
                subject = subj_m.group(1).strip()
                state = 'meta'
                continue
            if topic_m:
                topic = topic_m.group(1).strip()
                state = 'meta'
                continue
            if subtopic_m:
                state = 'question'  # question starts after Sub-Topic
                continue
            if opt_m:
                current_opt_key = ['A', 'B', 'C', 'D'][int(opt_m.group(1)) - 1]
                options[current_opt_key] = opt_m.group(2).strip()
                state = 'option'
                continue
            if ans_m:
                correct = normalize_answer(ans_m.group(1), 'numbered')
                state = 'done'
                continue

            if state == 'question':
                q_text_lines.append(line)
            elif state == 'option' and current_opt_key:
                # Continuation of current option
                if options[current_opt_key]:
                    options[current_opt_key] += ' ' + line
                else:
                    options[current_opt_key] = line

        q_text = ' '.join(q_text_lines).strip()
        if not q_text or not correct or len(options) < 2:
            continue

        final_subject = subject if subject else infer_subject(q_text)
        # Clean residual watermark chars from options
        clean_opts = {k: clean_option(v) for k, v in options.items()}

        questions.append({
            "id": make_id(year, shift, q_num),
            "year": year,
            "shift": shift,
            "questionNumber": q_num,
            "question": clean_option(q_text),
            "options": {k: clean_opts.get(k, '') for k in ['A', 'B', 'C', 'D']},
            "correctAnswer": correct,
            "explanation": "",
            "subject": final_subject,
            "topic": topic,
            "difficulty": infer_difficulty(q_text, options),
            "tags": [],
        })

    return questions


# ─────────────────────────────────────────────────────────────────────────────
# FORMAT D/E: 2024 Shift 1 & 2
# "Ques N. Question text\nA. Opt\nB. Opt\nC. Opt\nD. Opt\nAns. X"  (uppercase for S1)
# "Ques N. Question\na. Opt\nb. Opt\nc. Opt\nd. Opt\nAns. x"       (lowercase for S2)
# ─────────────────────────────────────────────────────────────────────────────

def extract_format_d(pdf_path: str, year: int, shift: int = 1) -> list:
    """2024 Shift 1 and Shift 2 format."""
    questions = []

    full_text = get_pdf_text(pdf_path)
    lines = [l.strip() for l in full_text.split('\n')
             if l.strip() and not (len(l.strip()) == 1 and l.strip() in _WM_CHARS)]

    # Find "Ques N." markers - handle "Ques N. text" on same line
    q_starts = []
    for i, line in enumerate(lines):
        m = re.match(r'^Ques\s+(\d+)\.\s*(.*)', line, re.IGNORECASE)
        if m:
            q_starts.append((i, int(m.group(1)), m.group(2).strip()))

    for idx, (start_line, q_num, first_text) in enumerate(q_starts):
        end_line = q_starts[idx + 1][0] if idx + 1 < len(q_starts) else len(lines)
        block = lines[start_line + 1:end_line]

        q_text_lines = [first_text] if first_text else []
        options = {}
        correct = ''
        state = 'question'

        # Option pattern: "A." or "a." at start of line
        opt_re = re.compile(r'^([A-Da-d])\.\s+(.*)', re.IGNORECASE)
        ans_re = re.compile(r'^Ans\.\s*([A-Da-d])', re.IGNORECASE)

        current_opt = None
        for line in block:
            ans_m = ans_re.match(line)
            if ans_m:
                correct = ans_m.group(1).upper()
                state = 'done'
                continue

            opt_m = opt_re.match(line)
            if opt_m:
                current_opt = opt_m.group(1).upper()
                options[current_opt] = opt_m.group(2).strip()
                state = 'option'
                continue

            if state == 'question':
                q_text_lines.append(line)
            elif state == 'option' and current_opt:
                options[current_opt] += ' ' + line

        q_text = ' '.join(q_text_lines).strip()
        if not q_text or not correct or len(options) < 2:
            continue

        clean_opts = {k: clean_option(v) for k, v in options.items()}
        questions.append({
            "id": make_id(year, shift, q_num),
            "year": year,
            "shift": shift,
            "questionNumber": q_num,
            "question": clean_option(q_text),
            "options": {k: clean_opts.get(k, '') for k in ['A', 'B', 'C', 'D']},
            "correctAnswer": correct,
            "explanation": "",
            "subject": infer_subject(q_text),
            "topic": "",
            "difficulty": infer_difficulty(q_text, options),
            "tags": [],
        })

    return questions


# ─────────────────────────────────────────────────────────────────────────────
# Dispatch table
# ─────────────────────────────────────────────────────────────────────────────

PDF_CONFIG = [
    ('data/pdfs/*2012*.pdf', 2012, 1, extract_format_a),
    ('data/pdfs/*2013*.pdf', 2013, 1, extract_format_a),
    ('data/pdfs/*2014*.pdf', 2014, 1, extract_format_a),
    ('data/pdfs/*2015*.pdf', 2015, 1, extract_format_a),
    ('data/pdfs/*2016*.pdf', 2016, 1, extract_format_a),
    ('data/pdfs/*2017*.pdf', 2017, 1, extract_format_b),
    ('data/pdfs/*2018*.pdf', 2018, 1, extract_format_a),
    ('data/pdfs/*2019*.pdf', 2019, 1, extract_format_a),
    ('data/pdfs/*2020*.pdf', 2020, 1, extract_format_a),
    # 2021 is a scanned image PDF — no extractable text
    ('data/pdfs/*2022*.pdf', 2022, 1, extract_format_c),
    ('data/pdfs/*2023*.pdf', 2023, 1, extract_format_c),
    ('data/pdfs/*2024*shift-1*.pdf', 2024, 1, extract_format_d),
    ('data/pdfs/*2024*shift-2*.pdf', 2024, 2, extract_format_d),
]


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def run_extraction():
    all_questions = []
    report = {
        "totalExtracted": 0,
        "byYear": {},
        "skipped": [],
        "issues": [],
        "questionsWithoutExplanation": 0,
        "questionsWithMissingOptions": 0,
        "incompleteOptions": 0,
    }

    for pattern, year, shift, extractor in PDF_CONFIG:
        files = glob.glob(pattern)
        if not files:
            msg = f"No file found: {pattern}"
            print(f"  WARN: {msg}")
            report['skipped'].append(msg)
            continue

        for pdf_path in sorted(files):
            label = f"{year} shift-{shift}: {os.path.basename(pdf_path)}"
            print(f"\nExtracting {label}")
            try:
                qs = extractor(pdf_path, year, shift)
                print(f"  → {len(qs)} questions extracted")

                for q in qs:
                    if not q['explanation']:
                        report['questionsWithoutExplanation'] += 1
                    missing = [k for k in ['A', 'B', 'C', 'D'] if not q['options'].get(k)]
                    if missing:
                        report['incompleteOptions'] += 1

                all_questions.extend(qs)
                key = f"{year}-shift{shift}"
                report['byYear'][key] = len(qs)

            except Exception as e:
                import traceback
                msg = f"Error in {label}: {e}"
                print(f"  ERROR: {msg}")
                print(traceback.format_exc())
                report['issues'].append(msg)

    report['skipped'].append(
        "2021: Scanned image PDF — text extraction not possible without OCR."
    )

    # Deduplicate
    seen = set()
    unique_qs = []
    for q in all_questions:
        if q['id'] not in seen:
            seen.add(q['id'])
            unique_qs.append(q)

    report['totalExtracted'] = len(unique_qs)

    print(f"\n{'='*60}")
    print(f"Total unique questions: {len(unique_qs)}")
    print(f"By year: {report['byYear']}")
    print(f"Without explanation: {report['questionsWithoutExplanation']}")
    print(f"Incomplete options: {report['incompleteOptions']}")
    print(f"{'='*60}")

    os.makedirs('data/extracted', exist_ok=True)
    with open('data/extracted/questions.json', 'w', encoding='utf-8') as f:
        json.dump(unique_qs, f, indent=2, ensure_ascii=False)

    with open('data/extracted/extraction_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nSaved → data/extracted/questions.json")
    print(f"Report → data/extracted/extraction_report.json")
    return unique_qs, report


if __name__ == '__main__':
    run_extraction()
