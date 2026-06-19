"""Visual search: feature & conjunction (Treisman & Gelade 1980)."""
from __future__ import annotations

import random

from .base import balanced_grid, fixation_phase, phase, text

SPEC = {
    "name": "Visual Search",
    "summary": ("Decide whether a target is present in an array, in feature "
                "(pop-out) and conjunction blocks. Search slope is ~flat for "
                "feature and steep for conjunction."),
    "references": [
        "Treisman, A. M., & Gelade, G. (1980). A feature-integration theory of "
        "attention. Cognitive Psychology, 12(1), 97-136.",
        "Wolfe, J. M. (1998). Visual search. In H. Pashler (Ed.), Attention "
        "(pp. 13-73). Psychology Press.",
    ],
    "conditions": ["feature", "conjunction"],
    "condition_balance": "~50% target-present / absent within each condition x set size",
    "task": "Is the TARGET present in the display? Present or Absent.",
    "surface": {
        "units": "height", "background": "gray",
        "stim_pos": [0.0, 0.0], "stim_height": 0.05, "layout_w": 0.7,
        "fixation_char": "+", "fixation_height": 0.04, "set_sizes": [4, 8, 16],
    },
    "timing": {"fixation_sec": 0.5, "max_response_sec": 5.0, "iti_sec": 1.0},
    "responses": {"mapping": {"present": "m", "absent": "z"}, "quit_key": "escape",
                  "note": "Array stays until response; positions re-randomised "
                          "each trial (size held constant)."},
    "dv": ["RT by condition x set size",
           "search slope ms/item (feature flat vs conjunction steep)"],
}


def _item(letter, color, pos, h):
    return text(letter, color=color, pos=pos, height=h)


def build_trials(set_sizes=(4, 8, 16), reps: int = 5, seed: int = 0) -> list[dict]:
    rng = random.Random(seed)
    S = SPEC["surface"]
    m = SPEC["responses"]["mapping"]
    keys = list(m.values())
    h = S["stim_height"]

    trials = []
    for _ in range(reps):
        for cond in SPEC["conditions"]:
            for size in set_sizes:
                for present in (True, False):
                    pos = balanced_grid(layout_w=S["layout_w"], n=size,
                                        rng=rng)
                    stims = []
                    if cond == "feature":      # target blue T among brown T
                        target = ("T", "blue")
                        distractors = [("T", "brown")]
                    else:                       # conjunction: green T among green X + brown T
                        target = ("T", "green")
                        distractors = [("X", "green"), ("T", "brown")]
                    for i, p in enumerate(pos):
                        if present and i == 0:
                            ltr, col = target
                        else:
                            ltr, col = rng.choice(distractors)
                        stims.append(_item(ltr, col, p, h))
                    ckey = m["present"] if present else m["absent"]
                    trials.append({
                        "condition": cond,
                        "phases": [fixation_phase(SPEC),
                                   phase(stims, dur=SPEC["timing"]["max_response_sec"],
                                         collect=True, keys=keys)],
                        "correct_key": ckey,
                        "rt_phase": 1,
                        "meta": {"set_size": size, "present": int(present)},
                    })
    rng.shuffle(trials)
    return trials
