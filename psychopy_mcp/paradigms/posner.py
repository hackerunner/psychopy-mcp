"""Posner spatial cueing task (Posner 1980)."""
from __future__ import annotations

import random

from .base import fixation, phase, rect

SPEC = {
    "name": "Posner Spatial Cueing",
    "summary": ("Detect a peripheral target after a (mostly valid) location cue. "
                "Validity effect = invalid RT - valid RT, indexing covert "
                "attentional orienting."),
    "references": [
        "Posner, M. I. (1980). Orienting of attention. Quarterly Journal of "
        "Experimental Psychology, 32(1), 3-25.",
        "Posner, M. I., Snyder, C. R. R., & Davidson, B. J. (1980). Attention "
        "and the detection of signals. JEP: General, 109(2), 160-174.",
    ],
    "conditions": ["valid", "invalid"],
    "condition_balance": "80% valid / 20% invalid (directional peripheral cue)",
    "task": "Keep eyes on the centre. Press SPACE as soon as you see the target.",
    "surface": {
        "units": "height", "background": "black",
        "stim_pos": [0.0, 0.0], "box_left": [-0.35, 0.0], "box_right": [0.35, 0.0],
        "box_size": 0.12, "target_size": 0.06, "fixation_char": "+",
        "fixation_height": 0.04,
    },
    "timing": {"fixation_sec": 0.5, "cue_sec": 0.1, "soa_sec": 0.5,
               "max_response_sec": 1.5, "iti_sec": 1.0},
    "responses": {"mapping": {"detect": "space"}, "quit_key": "escape",
                  "note": "Detection version (single key); CTOA = soa_sec."},
    "dv": ["RT", "validity effect = invalid RT - valid RT"],
}


def _boxes(S, cued=None):
    out = []
    for side, pos in (("left", S["box_left"]), ("right", S["box_right"])):
        bright = "yellow" if side == cued else "white"
        out.append(rect(pos=pos, size=[S["box_size"], S["box_size"]],
                        lineColor=bright))
    return out


def build_trials(valid_reps: int = 16, invalid_reps: int = 4, seed: int = 0) -> list[dict]:
    rng = random.Random(seed)
    S, T = SPEC["surface"], SPEC["timing"]
    pos_of = {"left": S["box_left"], "right": S["box_right"]}

    plan = []  # (target_side, cue_side, validity)
    for tside in ("left", "right"):
        plan += valid_reps * [(tside, tside, "valid")]
        other = "right" if tside == "left" else "left"
        plan += invalid_reps * [(tside, other, "invalid")]

    isi = max(T["soa_sec"] - T["cue_sec"], 0.0)
    trials = []
    for (tside, cside, validity) in plan:
        target = rect(pos=pos_of[tside], size=[S["target_size"], S["target_size"]],
                      fillColor="white", lineColor="white")
        trials.append({
            "condition": validity,
            "phases": [
                phase([fixation(SPEC)] + _boxes(S), dur=T["fixation_sec"]),
                phase([fixation(SPEC)] + _boxes(S, cued=cside), dur=T["cue_sec"]),
                phase([fixation(SPEC)] + _boxes(S), dur=isi),
                phase([fixation(SPEC)] + _boxes(S) + [target],
                      dur=T["max_response_sec"], collect=True, keys=["space"]),
            ],
            "correct_key": "space",
            "rt_phase": 3,
            "meta": {"target_side": tside, "cue_side": cside},
        })
    rng.shuffle(trials)
    return trials
