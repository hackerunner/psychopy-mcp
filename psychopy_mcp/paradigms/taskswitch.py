"""Cued task-switching task (Meiran 1996; Monsell 2003)."""
from __future__ import annotations

import random

from .base import fixation_phase, phase, text

SPEC = {
    "name": "Cued Task-Switching",
    "summary": ("A cue selects which of two judgments to make on a bivalent "
                "digit; the task randomly switches or repeats. Switch cost = "
                "switch RT - repeat RT."),
    "references": [
        "Meiran, N. (1996). Reconfiguration of processing mode prior to task "
        "performance. JEP: LMC, 22(6), 1423-1442.",
        "Monsell, S. (2003). Task switching. Trends in Cognitive Sciences, "
        "7(3), 134-140.",
    ],
    "conditions": ["switch", "repeat"],
    "condition_balance": "random task order => ~50% switch / ~50% repeat",
    "task": "Follow the CUE: PARITY = odd/even, MAGNITUDE = low/high (<5 / >5).",
    "surface": {
        "units": "height", "background": "gray",
        "stim_pos": [0.0, 0.0], "cue_pos": [0.0, 0.15], "stim_height": 0.10,
        "cue_height": 0.06, "fixation_char": "+", "fixation_height": 0.05,
    },
    "timing": {"fixation_sec": 0.5, "cue_stim_interval_sec": 0.6,
               "max_response_sec": 3.0, "iti_sec": 0.5},
    "responses": {"mapping": {"z": "odd / low (<5)", "m": "even / high (>5)"},
                  "quit_key": "escape",
                  "note": "Two keys reused across both tasks (bivalent target)."},
    "tasks": ["PARITY", "MAGNITUDE"],
    "digits": [1, 2, 3, 4, 6, 7, 8, 9],
    "dv": ["RT, accuracy", "switch cost = switch RT - repeat RT"],
}


def _correct(task, digit):
    if task == "PARITY":
        return "z" if digit % 2 == 1 else "m"        # odd->z, even->m
    return "z" if digit < 5 else "m"                 # low->z, high->m


def build_trials(n_trials: int = 64, seed: int = 0) -> list[dict]:
    rng = random.Random(seed)
    S, T = SPEC["surface"], SPEC["timing"]
    prev = None
    trials = []
    for i in range(n_trials):
        task = rng.choice(SPEC["tasks"])
        digit = rng.choice(SPEC["digits"])
        cond = "repeat" if (prev is None or task == prev) else "switch"
        prev = task
        cue = text(task, color="white", pos=S["cue_pos"], height=S["cue_height"])
        dig = text(str(digit), color="white", pos=S["stim_pos"], height=S["stim_height"])
        trials.append({
            "condition": cond,
            "phases": [
                fixation_phase(SPEC),
                phase([cue], dur=T["cue_stim_interval_sec"]),
                phase([cue, dig], dur=T["max_response_sec"], collect=True,
                      keys=["z", "m"]),
            ],
            "correct_key": _correct(task, digit),
            "rt_phase": 2,
            "meta": {"task": task, "digit": digit},
        })
    return trials   # sequence matters for switch/repeat; do NOT shuffle
