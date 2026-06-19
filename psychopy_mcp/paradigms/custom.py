"""Custom user-defined paradigms.

A custom paradigm is a JSON file under ``custom_paradigms/`` describing a simple
choice-RT task: a list of items (text + colour + condition + correct key) plus
shared surface/timing/response settings. It runs on the same engine as the
built-in paradigms, so it inherits the same guarantee — every item shares the
surface parameters declared once in the spec.

Schema (see create_template for a starting point):
    {
      "name": str, "summary": str, "custom": true,
      "surface": {units, background, stim_pos, stim_height,
                  fixation_char, fixation_height},
      "timing":  {fixation_sec, max_response_sec, iti_sec},
      "responses": {"mapping": {label: key, ...}, "quit_key": "escape"},
      "items": [ {"text": str, "color": str, "condition": str,
                  "correct_key": str|null}, ... ],
      "reps": int,
      "references": [str, ...]
    }
"""
from __future__ import annotations

import json
from pathlib import Path

from .base import fixation_phase, response_phase, text


def create_template(name: str) -> dict:
    """Return a minimal valid custom-paradigm spec to edit."""
    return {
        "name": name,
        "summary": f"Custom paradigm: {name}",
        "custom": True,
        "surface": {
            "units": "height", "background": "black",
            "stim_pos": [0.0, 0.0], "stim_height": 0.12,
            "fixation_char": "+", "fixation_height": 0.08,
        },
        "timing": {"fixation_sec": 0.5, "max_response_sec": 2.0, "iti_sec": 0.5},
        "responses": {"mapping": {"left": "f", "right": "j"}, "quit_key": "escape"},
        "items": [
            {"text": "EXAMPLE", "color": "white", "condition": "A", "correct_key": "f"},
        ],
        "reps": 10,
        "references": [],
    }


def save(spec: dict, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    key = "".join(c for c in spec["name"] if c.isalnum() or c in "-_").strip("-_").lower()
    path = directory / f"{key}.json"
    path.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate(spec: dict) -> list[str]:
    """Return a list of problems (empty = valid)."""
    errs = []
    for f in ("name", "surface", "timing", "responses", "items"):
        if f not in spec:
            errs.append(f"missing field: {f}")
    if not spec.get("items"):
        errs.append("items must be a non-empty list")
    keys = set(spec.get("responses", {}).get("mapping", {}).values())
    for i, it in enumerate(spec.get("items", [])):
        if "text" not in it:
            errs.append(f"item {i}: missing 'text'")
        ck = it.get("correct_key")
        if ck is not None and ck not in keys:
            errs.append(f"item {i}: correct_key {ck!r} not in response mapping {keys}")
    return errs


def build_trials(spec: dict, reps: int | None = None, seed: int = 0) -> list[dict]:
    import random
    rng = random.Random(seed)
    S = spec["surface"]
    keys = list(spec["responses"]["mapping"].values())
    reps = reps if reps is not None else spec.get("reps", 10)

    trials = []
    for _ in range(reps):
        for it in spec["items"]:
            stim = text(it["text"], color=it.get("color", "white"),
                        pos=S.get("stim_pos", [0, 0]),
                        height=S.get("stim_height", 0.12))
            trial = {
                "condition": it.get("condition", "default"),
                "phases": [fixation_phase(spec), response_phase([stim], spec, keys)],
                "rt_phase": 1,
                "meta": {"text": it["text"]},
            }
            if "correct_key" in it:
                trial["correct_key"] = it["correct_key"]
            trials.append(trial)
    rng.shuffle(trials)
    return trials
