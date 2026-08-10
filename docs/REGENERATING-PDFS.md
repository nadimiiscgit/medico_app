# Changing the PDFs without regenerating the content

Short version: **the study material is already stored as JSON, and re-rendering the
PDFs costs nothing.** You never have to pay for the same chapter twice. Tell me what
you want changed and I re-cut the PDFs from what is already on disk.

## The two layers

| | Where | Written by | Cost to redo |
|---|---|---|---|
| **Content** | `data/topics/chapters/<subject>/<topicId>.json` | an LLM, once per topic | ~45k tokens per chapter |
| **Questions** | `data/extracted/questions.json` + `medico-app/public/explanations.json` | extracted from the real papers | already done |
| **Layout** | `config/render.json` | you, by hand | free |
| **PDFs** | `output/pdf/*.pdf` | `pipeline/render_pdf.py`, pure reportlab | free, ~40 seconds |

`render_pdf.py` has never called a model. It reads chapter JSON and lays it out. So
"make the font bigger", "drop the explanations", "tier A only" are all free — they are
re-renders, not regenerations.

The chapter JSON is the asset. It survives every layout change, and it is what should
be backed up.

## Chapter JSON

```json
{
  "topicId": "microbiology.mycology.opportunistic-mycoses",
  "topic": "Opportunistic Mycoses", "subject": "Microbiology",
  "section": "Mycology", "tier": "A", "highYield": 1.31, "pyqCount": 43,
  "oneLiner": "...",
  "mustKnow": ["...", "..."],
  "sections": [
    {"type": "concept",  "heading": "...", "body": "..."},
    {"type": "table",    "heading": "...", "columns": [...], "rows": [[...]]},
    {"type": "repeats",  "items": [{"concept": "...", "years": [2019, 2023]}]},
    {"type": "pitfalls", "items": ["..."]},
    {"type": "crossref", "items": [{"book": "...", "chapter": "...", "note": "..."}]},
    {"type": "pyqBank",  "questionIds": ["neetpg-2023-s1-q0042", "..."]}
  ]
}
```

Note `pyqBank` stores **ids only**. Stems, options, answers and explanations are pulled
from the corpus at render time, so a question can never drift from the real paper, and
fixing an answer key fixes it everywhere at once.

## Re-rendering

```bash
python3 -m pipeline.render_pdf --all --index --high-yield --calendar   # everything
python3 -m pipeline.render_pdf --subject Microbiology                  # one subject
```

## `config/render.json`

Every layout decision lives here. Edit the file, or override one key for a single run
with `--set`. Missing keys fall back to the defaults, so the file can hold only what
you actually changed.

```bash
python3 -m pipeline.render_pdf --all --set layout.fontScale=1.15
python3 -m pipeline.render_pdf --all --set questions.answerKey.explanations=false
python3 -m pipeline.render_pdf --write-config    # rewrite the file with every default
```

| Key | Default | What it does |
|---|---|---|
| `theme.accent` / `.muted` / `.rule` / `.boxBackground` | blues | colours |
| `layout.fontScale` | `1.0` | scales every font at once; `1.15` is easier to read, ~15% more pages |
| `layout.marginMm` | `18` | page margin |
| `layout.coverPage` / `.tableOfContents` / `.runningHeader` / `.pageNumbers` | `true` | turn off the furniture |
| `questions.include` | `"all"` | `all`, `scheduled` (only what the calendar budgets time for), `none` (chapters only) |
| `questions.answersInline` | `false` | `true` puts the answer back under each question instead of in the key |
| `questions.answerKey.include` | `true` | `false` prints no answers at all — a clean mock paper |
| `questions.answerKey.grid` | `true` | the compact `Q1 A, Q2 C` marking grid |
| `questions.answerKey.explanations` | `true` | the long explanations after the grid |
| `questions.answerKey.explanationChars` | `1600` | truncation point for one explanation |
| `questions.flagMissingImages` | `true` | the orange "Image not available" warning |
| `questions.showImages` | `true` | embed question images |
| `questions.markScheduled` | `true` | the ★ ON THE PLAN badge |
| `questions.showSourceBadge` | `true` | the "NEET PG 2023" line under each question |
| `chapters.tiers` | `["A","B","C"]` | which tiers to print; `--set chapters.tiers=A` for a crunch-week edition |
| `chapters.include.*` | all `true` | drop any section type: `oneLiner`, `mustKnow`, `concept`, `table`, `mnemonic`, `pitfalls`, `repeats`, `crossref` |

### Recipes

```bash
# Blind mock paper — questions only, no answers anywhere
python3 -m pipeline.render_pdf --all --set questions.answerKey.include=false

# Last-week revision — tier A, must-know and tables only, no question banks
python3 -m pipeline.render_pdf --all \
  --set chapters.tiers=A --set questions.include=none \
  --set chapters.include.concept=false --set chapters.include.crossref=false

# Only the questions the calendar actually schedules
python3 -m pipeline.render_pdf --all --set questions.include=scheduled

# Bigger type for reading on a phone
python3 -m pipeline.render_pdf --all --set layout.fontScale=1.2
```

## What still costs tokens

Only **writing a chapter that does not exist yet**. 15 of 320 planned chapters are
written. Everything else — layout, ordering, the calendar, answer keys, tier filters,
fixing a wrong answer key — is free and repeatable.

If you want a change to the *wording* of a chapter, that is an edit to one JSON file,
not a regeneration; ask for it by topic and it is cheap.
