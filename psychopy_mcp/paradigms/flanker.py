"""Eriksen Flanker task (Eriksen & Eriksen 1974)."""
from __future__ import annotations

import random

from .base import fixation_phase, response_phase, text

SPEC = {
    "name": "Eriksen Flanker",
    "summary": ("Identify the direction of the central arrow while ignoring "
                "flanking arrows. Flanker effect = slower responding on "
                "incongruent vs congruent trials."),
    "references": [
        "Eriksen, B. A., & Eriksen, C. W. (1974). Effects of noise letters upon "
        "the identification of a target letter in a nonsearch task. Perception "
        "& Psychophysics, 16(1), 143-149.",
        "Kopp, B., Rist, F., & Mattler, U. (1996). N200 in the flanker task as a "
        "neurobehavioral tool. Psychophysiology, 33(3), 282-294.",
    ],
    "conditions": ["congruent", "incongruent", "neutral"],
    "condition_balance": "equal; left/right correct response equiprobable",
    "task": "Respond to the direction the CENTRE arrow points; ignore the others.",
    "surface": {
        "units": "height", "background": "black",
        "stim_pos": [0.0, 0.0], "stim_height": 0.10, "font": "Consolas",
        "fixation_char": "+", "fixation_height": 0.05,
    },
    "timing": {"fixation_sec": 0.5, "max_response_sec": 1.0, "iti_sec": 0.5},
    "responses": {
        "mapping": {"left": "left", "right": "right"},
        "quit_key": "escape",
        "note": "Spatially compatible mapping; no key counterbalancing needed.",
    },
    "dv": ["RT (correct)", "accuracy",
           "flanker effect = RT(incongruent) - RT(congruent)"],
}

_ARROW = {"left": "<", "right": ">"}


def build_trials(reps: int = 40, seed: int = 0) -> list[dict]:
    rng = random.Random(seed)
    S = SPEC["surface"]
    keys = list(SPEC["responses"]["mapping"].values())

    combos = []  # (target_dir, condition, display)
    for tdir in ("left", "right"):
        a = _ARROW[tdir]
        o = _ARROW["right" if tdir == "left" else "left"]
        combos.append((tdir, "congruent", a * 5))
        combos.append((tdir, "incongruent", o * 2 + a + o * 2))
        combos.append((tdir, "neutral", "--" + a + "--"))

    trials = []
    for _ in range(reps):
        for (tdir, cond, disp) in combos:
            stim = text(disp, color="white", pos=S["stim_pos"],
                        height=S["stim_height"], font=S["font"])
            trials.append({
                "condition": cond,
                "phases": [fixation_phase(SPEC), response_phase([stim], SPEC, keys)],
                "correct_key": tdir,
                "rt_phase": 1,
                "meta": {"target_dir": tdir, "display": disp},
            })
    rng.shuffle(trials)
    return trials
