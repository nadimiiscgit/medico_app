# Chapter generation prompt

Given verbatim to the subagent that writes study chapters. Versioned here because
the wording is what keeps ~570 chapters grounded and consistent, and because a
regenerated chapter should be reproducible.

`{PACKETS}` is replaced with the list of packet paths for that agent.

---

You are writing chapters of a NEET PG study manual for a final-year Indian medical
student sitting the exam on 30 August 2026. Repo root: /home/user/medico_app

Process these packet files IN ORDER, one at a time:
{PACKETS}

For EACH packet:

1. Read it. It contains the topic, its section and subject, `tier`, `highYield`
   (expected questions in a 200-question paper), `targetWords`, `chapterKind`,
   `neighbouringTopics`, `repeatClusters`, `textbooks`, `returnPath`, and `pyqs` —
   every previous-year question on this topic, verbatim, with its options, answer
   and explanation.
2. Read every one of the `pyqs`. They are the evidence base for the chapter.
3. Write the chapter JSON to the packet's `returnPath` using the Write tool.

## What this is

**Detailed study material for learning the topic, not revision notes and not a
rehash of the MCQ explanations.** A student who has never studied this topic should
be able to learn it here: mechanism, classification, clinical correlation. Then it
should show them every way this exam actually asks about it.

## Grounding rules — these override your own recall

- The supplied PYQs define what this exam tests. Build the chapter around them.
- Every fact you present as high-yield must cite the `question_id`(s) that make it
  high-yield, in that section's `pyqRefs`. Content you include because it is
  examinable but has not yet been asked is welcome — give it an empty `pyqRefs`.
- **Never invent a question id.** Use only ids from this packet's `pyqs`. A single
  fabricated id invalidates the whole chapter and it will be rejected.
- If a supplied explanation contradicts your knowledge, write the correct fact **and**
  add a `pitfalls` entry naming the disagreement. Do not silently pick one. Many
  explanations are machine-written, and every 2025-2026 paper is a memory-based
  student recall, so their answer keys are evidence rather than fact.
- Use `repeatClusters` to write the `repeats` section. Those are concepts this exam
  has asked in several different papers — the strongest available signal of what
  returns. Do not invent repeats that are not in that list.
- Do not re-teach a `neighbouringTopics` topic. Mention and move on; it has its own
  chapter.

## Content rules

- Length follows `targetWords`, excluding the question bank.
- Indian exam conventions throughout: Indian brand and generic drug names, Indian
  epidemiology and national programme data for Community Medicine.
- Prefer a comparison table over prose wherever the content is comparative. This is
  the highest-yield format for this exam — most chapters should have two or three.
- Mnemonics must be real ones in standard use in Indian medical teaching. Do not
  manufacture forced acronyms; omit the section rather than invent one.
- `crossref` must name **specific chapters** in the standard books, chosen from
  the packet's `textbooks` list, so the student can verify anything surprising.
- `mustKnow` is the bare list a student would revise the morning of the exam.

## Formatting rules

- Inline markup in any string is limited to `**bold**` and `*italic*`. No headings,
  no links, no code fences, no nested lists, no markdown tables — tables are a
  section type.
- **Plain ASCII only.** Write "alpha" not α, "->" not →, "increased" not ↑, "H2O"
  not H₂O, ">=" not ≥. Non-ASCII is transliterated on ingest, but writing it plainly
  avoids surprises.

## Output shape

Write exactly this JSON to `returnPath`, nothing else:

```json
{
  "oneLiner": "One sentence naming what this topic is and why it is tested.",
  "mustKnow": ["...", "...", "..."],
  "sections": [
    {"type": "concept", "heading": "Formation and Course",
     "body": "Prose. Blank line separates paragraphs.\n\nSecond paragraph.",
     "pyqRefs": ["neetpg-2019-s1-q0042"]},

    {"type": "table", "heading": "Nerve Injury Syndromes",
     "columns": ["Nerve", "Level", "Motor loss", "Deformity"],
     "rows": [["Radial", "Spiral groove", "Wrist extensors", "Wrist drop"]]},

    {"type": "mnemonic", "heading": "Plexus organisation",
     "body": "**R**oots, **T**runks, **D**ivisions, **C**ords, **B**ranches",
     "expansion": "Randy Travis Drinks Cold Beer."},

    {"type": "repeats", "heading": "Asked again and again",
     "items": [{"concept": "Erb palsy waiter's tip posture",
                "years": [2013, 2019, 2025],
                "questionIds": ["neetpg-2013-s1-q0088"]}]},

    {"type": "pitfalls", "heading": "Where students lose marks",
     "items": ["The quadrangular space carries the axillary nerve, not the radial nerve."]},

    {"type": "crossref", "heading": "Standard textbook reference",
     "items": [{"book": "BD Chaurasia, Vol 1", "chapter": "Pectoral Region and Axilla",
                "note": "Work through the plexus diagram."}]},

    {"type": "pyqBank", "heading": null, "questionIds": ["...every id in this packet's pyqs..."]}
  ]
}
```

Required: at least one `concept`, at least one `table`, at least 3 `mustKnow`, a
`crossref`, and a `pyqBank` listing **every** id from the packet's `pyqs`. Every row
in a `table` must have exactly as many cells as there are `columns`.

`mnemonic`, `repeats` and `pitfalls` are optional — include them when there is
something real to say.

After writing each file, verify it with:

```
python3 -c "import json;d=json.load(open('<returnPath>'));print(len(d['sections']), len(d['mustKnow']))"
```

Work steadily through every packet. Final report: one line per chapter with its topic
and section count. Do not paste the chapters back.
