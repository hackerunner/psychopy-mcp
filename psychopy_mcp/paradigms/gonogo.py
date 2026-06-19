"""Go/No-Go task (response inhibition; Wessel 2018)."""
from __future__ import annotations

import random

from .base import circle, fixation_phase, phase

SPEC = {
    "name": "Go/No-Go Task",
    "summary": ("Press for frequent Go stimuli, withhold for infrequent No-Go "
                "stimuli. Commission errors (presses to No-Go) index failed "
                "response inhibition."),
    "references": [
        "Wessel, J. R. (2018). Prepotent motor activity and inhibitory control "
        "demands in different variants of the go/no-go paradigm. "
        "Psychophysiology, 55(3), e12871.",
        "Verbruggen, F., & Logan, G. D. (2008). Automatic and controlled "
        "response inhibition. JEP: General, 137(4), 649-672.",
    ],
    "conditions": ["go", "nogo"],
    "condition_balance": "Go 75% / No-Go 25% (prepotency-inducing 3:1)",
    "task": "Press SPACE for the GREEN circle; do NOT press for the RED circle.",
    "surface": {
        "units": "height", "background": "gray",
        "stim_pos": [0.0, 0.0], "stim_radius": 0.12,
        "fixation_char": "+", "fixation_height": 0.05,
        "go_color": "lime", "nogo_color": "red",
    },
    "timing": {"fixation_sec": 0.25, "stim_sec": 0.5, "max_response_sec": 1.0,
               "iti_sec": 0.5},
    "responses": {
        "mapping": {"go": "space"}, "quit_key": "escape",
        "note": "Single key for Go; No-Go requires withholding.",
    },
    "dv": ["commission error rate (presses to No-Go)", "Go RT", "omission rate"],
}


def build_trials(go_reps: int = 75, nogo_reps: int = 25, seed: int = 0) -> list[dict]:
    rng = random.Random(seed)
    S = SPEC["surface"]
    trials = []
    for cond, n, color, ckey in (
        ("go", go_reps, S["go_color"], "space"),
        ("nogo", nogo_reps, S["nogo_color"], None),
    ):
        for _ in range(n):
            stim = circle(pos=S["stim_pos"], radius=S["stim_radius"],
                          fillColor=color, lineColor=color)
            trials.append({
                "condition": cond,
                "phases": [fixation_phase(SPEC),
                           phase([stim], dur=SPEC["timing"]["max_response_sec"],
                                 collect=True, keys=["space"])],
                "correct_key": ckey,   # None on No-Go = correct to withhold
                "rt_phase": 1,
                "meta": {"stim_color": color},
            })
    rng.shuffle(trials)
    return trials
