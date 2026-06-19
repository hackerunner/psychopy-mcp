"""Attention Network Test (Fan et al. 2002)."""
from __future__ import annotations

import random

from .base import fixation, phase, text

SPEC = {
    "name": "Attention Network Test (ANT)",
    "summary": ("Identify a central arrow's direction amid flankers, under four "
                "cue conditions. Yields alerting, orienting and executive "
                "(conflict) network scores from RT differences."),
    "references": [
        "Fan, J., McCandliss, B. D., Sommer, T., Raz, A., & Posner, M. I. (2002). "
        "Testing the efficiency and independence of attentional networks. "
        "Journal of Cognitive Neuroscience, 14(3), 340-347.",
        "Fan, J., et al. (2005). The activation of attentional networks. "
        "NeuroImage, 26(2), 471-479.",
    ],
    "conditions": ["nocue", "centercue", "doublecue", "spatialcue"],
    "condition_balance": "4 cue x 3 flanker x 2 location x 2 direction, balanced",
    "task": "Press LEFT/RIGHT for the CENTRE arrow's direction; ignore flankers.",
    "surface": {
        "units": "height", "background": "gray",
        "stim_pos": [0.0, 0.0], "row_above": [0.0, 0.10], "row_below": [0.0, -0.10],
        "stim_height": 0.045, "font": "Consolas", "cue_char": "*",
        "fixation_char": "+", "fixation_height": 0.04, "stim_color": "black",
    },
    "timing": {"fixation_sec": 0.4, "cue_sec": 0.1, "soa_sec": 0.5,
               "max_response_sec": 1.7, "iti_sec": 1.0},
    "responses": {"mapping": {"left": "left", "right": "right"},
                  "quit_key": "escape",
                  "note": "Cue-target SOA fixed 500 ms (cue 100 ms + 400 ms)."},
    "dv": ["RT, accuracy per condition",
           "Alerting = nocue - doublecue; Orienting = centercue - spatialcue; "
           "Executive = incongruent - congruent"],
}

_A = {"left": "<", "right": ">"}


def _row(target_dir, flanker):
    a = _A[target_dir]
    o = _A["right" if target_dir == "left" else "left"]
    if flanker == "congruent":
        return a * 5
    if flanker == "incongruent":
        return o * 2 + a + o * 2
    return "--" + a + "--"   # neutral


def build_trials(reps: int = 1, seed: int = 0) -> list[dict]:
    rng = random.Random(seed)
    S, T = SPEC["surface"], SPEC["timing"]
    pos_of = {"above": S["row_above"], "below": S["row_below"]}
    isi = max(T["soa_sec"] - T["cue_sec"], 0.0)

    cells = []
    for cue in SPEC["conditions"]:
        for flanker in ("congruent", "incongruent", "neutral"):
            for loc in ("above", "below"):
                for tdir in ("left", "right"):
                    cells.append((cue, flanker, loc, tdir))

    def cue_stims(cue, loc):
        c = S["cue_char"]
        if cue == "nocue":
            return [fixation(SPEC)]
        if cue == "centercue":
            return [text(c, color="black", pos=S["stim_pos"], height=S["stim_height"])]
        if cue == "doublecue":
            return [fixation(SPEC),
                    text(c, color="black", pos=S["row_above"], height=S["stim_height"]),
                    text(c, color="black", pos=S["row_below"], height=S["stim_height"])]
        return [fixation(SPEC),
                text(c, color="black", pos=pos_of[loc], height=S["stim_height"])]

    trials = []
    for _ in range(reps):
        for (cue, flanker, loc, tdir) in cells:
            row = text(_row(tdir, flanker), color=S["stim_color"], pos=pos_of[loc],
                       height=S["stim_height"], font=S["font"])
            trials.append({
                "condition": cue,
                "phases": [
                    phase([fixation(SPEC)], dur=T["fixation_sec"]),
                    phase(cue_stims(cue, loc), dur=T["cue_sec"]),
                    phase([fixation(SPEC)], dur=isi),
                    phase([fixation(SPEC), row], dur=T["max_response_sec"],
                          collect=True, keys=["left", "right"]),
                ],
                "correct_key": tdir,
                "rt_phase": 3,
                "meta": {"cue": cue, "flanker": flanker, "location": loc,
                         "target_dir": tdir},
            })
    rng.shuffle(trials)
    return trials
