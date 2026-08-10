"""What the PDFs look like, as data rather than as code.

The study material is stored in two layers that cost very different things:

    data/topics/chapters/**.json   written once by an LLM   expensive
    output/pdf/*.pdf               rendered by reportlab    free

Rendering has never called a model — it reads the chapter JSON and lays it out.
But every layout decision used to be a literal in `render_pdf.py`, so "put the
answer key back inline" or "drop the explanations from the key" still meant
editing Python. This module moves those decisions into `config/render.json`,
so a change is a one-line edit and a re-render, and the chapters are never
touched.

    python3 -m pipeline.render_pdf --all --set questions.answerKey.grid=false

Anything not named in the file keeps the default below, so the file can hold
only what you actually changed.
"""
from __future__ import annotations

import copy
import json

from . import paths

DEFAULTS: dict = {
    "theme": {
        "accent": "#1f4e79",
        "muted": "#5a6472",
        "rule": "#c9d2dd",
        "boxBackground": "#f4f7fa",
    },
    "layout": {
        # Scales every font size at once. 1.1 is noticeably easier on the eyes
        # and costs about 10% more pages.
        "fontScale": 1.0,
        "marginMm": 18.0,
        "coverPage": True,
        "tableOfContents": True,
        "runningHeader": True,
        "pageNumbers": True,
    },
    "questions": {
        # all       every question the chapter carries
        # scheduled only the ones the calendar budgets time for
        # none      chapters only, no question banks
        "include": "all",
        # False keeps the questions attemptable and moves answers to the back.
        "answersInline": False,
        "answerKey": {
            "include": True,
            "grid": True,
            "explanations": True,
            "explanationChars": 1600,
        },
        "flagMissingImages": True,
        "showImages": True,
        "markScheduled": True,
        "showSourceBadge": True,
    },
    "chapters": {
        "tiers": ["A", "B", "C"],
        # Turn off any chapter section type you do not want printed.
        "include": {
            "oneLiner": True,
            "mustKnow": True,
            "concept": True,
            "table": True,
            "mnemonic": True,
            "pitfalls": True,
            "repeats": True,
            "crossref": True,
        },
    },
}


def _merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in (over or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def _coerce(text: str, current=None):
    """CLI overrides arrive as strings; make them the type the default is.

    `current` is the value being replaced, so a setting whose default is a list
    stays a list even when given one element — and so `questions.include=none`
    stays the string "none" rather than becoming a null.
    """
    if isinstance(current, str):
        return text
    if isinstance(current, list):
        return [p.strip() for p in text.split(",") if p.strip()]
    lowered = text.strip().lower()
    if lowered in ("true", "false"):
        return lowered == "true"
    if lowered == "null":
        return None
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    if text.startswith("[") or text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    if "," in text:
        return [p.strip() for p in text.split(",") if p.strip()]
    return text


def _assign(cfg: dict, dotted: str, raw: str) -> None:
    parts = dotted.split(".")
    node = cfg
    for part in parts[:-1]:
        if not isinstance(node.get(part), dict):
            raise SystemExit(f"unknown config path: {dotted}")
        node = node[part]
    if parts[-1] not in node:
        raise SystemExit(f"unknown config key: {dotted}")
    node[parts[-1]] = _coerce(raw, node[parts[-1]])


def load(path=None, overrides: list[str] | None = None) -> dict:
    """Defaults, then the config file, then any --set overrides."""
    path = paths.RENDER_CONFIG if path is None else paths.Path(path)
    cfg = copy.deepcopy(DEFAULTS)
    if path.exists():
        with open(path) as f:
            cfg = _merge(cfg, json.load(f))
    for item in overrides or []:
        if "=" not in item:
            raise SystemExit(f"--set expects key=value, got {item!r}")
        key, _, raw = item.partition("=")
        _assign(cfg, key.strip(), raw)
    return cfg


def write_default(path=None) -> "paths.Path":
    """Write the full default config out, so every knob is discoverable."""
    path = paths.RENDER_CONFIG if path is None else paths.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(DEFAULTS, f, indent=2)
        f.write("\n")
    return path


def add_args(parser) -> None:
    parser.add_argument("--config", help="render config JSON (default config/render.json)")
    parser.add_argument("--set", action="append", dest="overrides", metavar="KEY=VALUE",
                        help="override one config key, e.g. --set layout.fontScale=1.1")
