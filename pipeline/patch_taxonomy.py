"""Add topics the first tagging pass proved were missing.

The taxonomies were designed from a 200-question sample per subject, so topics
that are real but thinly represented in that sample got left out. Tagging the
full corpus surfaces them: the classifier returns UNSURE rather than forcing a
question into a topic it does not belong to, and the UNSURE list is therefore a
direct readout of what the taxonomy lacks.

Medicine ran at 19% UNSURE, and inspection showed two causes. Genuine gaps are
fixed here. The rest were questions filed under the wrong subject in the
original corpus — orthopaedic, ophthalmology and obstetric stems sitting inside
Medicine — which no Medicine topic could legitimately absorb; those are handled
by the sweep, which is allowed to move a question to another subject.

Usage:
    python3 -m pipeline.patch_taxonomy --dry-run
    python3 -m pipeline.patch_taxonomy --commit
"""
from __future__ import annotations

import argparse
import json
import re

from . import paths

# subject -> section -> [topic definitions]
GAPS: dict[str, dict[str, list[dict]]] = {
    "Medicine": {
        "Nephrology": [
            {"topic": "Urinary Tract Infection & Nephrolithiasis",
             "aliases": ["Renal stones", "Pyelonephritis"],
             "keywords": ["nephrolithiasis", "renal calculus", "staghorn",
                          "pyelonephritis", "struvite", "cystinuria",
                          "urinary tract infection", "dysuria", "vesicoureteric reflux"]},
        ],
        "Respiratory Medicine": [
            {"topic": "Sleep-Disordered Breathing",
             "aliases": ["Obstructive sleep apnoea", "OSA"],
             "keywords": ["obstructive sleep apnoea", "sleep apnea", "polysomnography",
                          "apnoea hypopnoea index", "cpap", "pickwickian",
                          "obesity hypoventilation", "epworth"]},
        ],
        "Rheumatology": [
            {"topic": "Osteoarthritis & Soft Tissue Rheumatism",
             "aliases": ["Degenerative joint disease"],
             "keywords": ["osteoarthritis", "heberden", "bouchard", "osteophyte",
                          "joint space narrowing", "fibromyalgia", "bursitis",
                          "plantar fasciitis"]},
        ],
        "Cardiology": [
            {"topic": "Peripheral Arterial & Venous Disease",
             "aliases": ["PAD", "Deep vein thrombosis"],
             "keywords": ["ankle brachial", "intermittent claudication", "buerger",
                          "varicose vein", "deep vein thrombosis", "leriche",
                          "raynaud", "thromboangiitis obliterans"]},
        ],
        "Gastroenterology & Hepatology": [
            {"topic": "Acute & Chronic Pancreatitis",
             "aliases": ["Pancreatic disease"],
             "keywords": ["pancreatitis", "ranson", "balthazar", "lipase",
                          "pseudocyst", "pancreatic calcification", "steatorrhoea"]},
        ],
        "Haematology & Oncology": [
            {"topic": "Principles of Oncology & Tumour Markers",
             "aliases": ["Paraneoplastic syndromes", "Cancer staging"],
             "keywords": ["tumour marker", "tumor marker", "paraneoplastic",
                          "tnm staging", "ca 125", "alpha fetoprotein",
                          "carcinoembryonic", "performance status"]},
            {"topic": "Bone Marrow Failure & Aplastic Anaemia",
             "aliases": ["Pancytopenia"],
             "keywords": ["aplastic anaemia", "aplastic anemia", "fanconi anaemia",
                          "pancytopenia", "pure red cell aplasia",
                          "myelodysplastic", "antithymocyte globulin"]},
        ],
        "Infectious Diseases": [
            {"topic": "Sexually Transmitted Infections",
             "aliases": ["STI", "Venereal disease"],
             "keywords": ["syphilis", "chancroid", "lymphogranuloma venereum",
                          "gonorrhoea", "donovanosis", "vdrl", "treponema pallidum",
                          "genital ulcer"]},
        ],
        "Neurology": [
            {"topic": "Coma, Raised Intracranial Pressure & Brain Death",
             "aliases": ["Head injury", "Glasgow Coma Scale"],
             "keywords": ["glasgow coma", "raised intracranial pressure", "papilloedema",
                          "brain death", "decerebrate", "decorticate", "cushing reflex",
                          "extradural haematoma", "subdural haematoma"]},
        ],
    },
}


def slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return re.sub(r"-{2,}", "-", s)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--commit", action="store_true")
    args = ap.parse_args()

    with open(paths.TAXONOMY) as f:
        tax = json.load(f)

    added = skipped = 0
    for subject, sections in GAPS.items():
        payload = tax["subjects"].get(subject)
        if payload is None:
            raise SystemExit(f"subject {subject!r} not in taxonomy")
        existing = {t["topic"].lower()
                    for sec in payload["sections"] for t in sec["topics"]}
        by_name = {sec["section"]: sec for sec in payload["sections"]}

        for section, topics in sections.items():
            target = by_name.get(section)
            if target is None:
                raise SystemExit(f"section {section!r} not in {subject}")
            for spec in topics:
                if spec["topic"].lower() in existing:
                    skipped += 1
                    continue
                target["topics"].append({
                    "id": f"{slug(subject)}.{slug(section)}.{slug(spec['topic'])}",
                    "topic": spec["topic"],
                    "aliases": spec.get("aliases", []),
                    "keywords": [k.lower() for k in spec["keywords"]],
                })
                added += 1
                print(f"  + {subject} / {section} / {spec['topic']}")

    total = sum(len(sec["topics"]) for s in tax["subjects"].values()
                for sec in s["sections"])
    print(f"\nadded {added}, already present {skipped}, taxonomy now {total} topics")

    if args.dry_run:
        print("DRY RUN — nothing written. Re-run with --commit.")
        return
    tmp = paths.TAXONOMY.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(tax, f, ensure_ascii=False, indent=2)
    with open(tmp) as f:
        json.load(f)
    tmp.replace(paths.TAXONOMY)
    print(f"written to {paths.TAXONOMY.relative_to(paths.REPO)}")


if __name__ == "__main__":
    main()
