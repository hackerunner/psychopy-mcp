"""Dot-probe task (MacLeod, Mathews & Tata 1986)."""
from __future__ import annotations

import random

from .base import fixation, fixation_phase, phase, text

SPEC = {
    "name": "Dot-Probe (Attentional Bias)",
    "summary": ("A threat and a neutral word are shown as a vertical pair, then "
                "a probe replaces one. Faster RT when the probe replaces the "
                "threat word indicates attentional bias toward threat."),
    "references": [
        "MacLeod, C., Mathews, A., & Tata, P. (1986). Attentional bias in "
        "emotional disorders. Journal of Abnormal Psychology, 95(1), 15-20.",
        "Mogg, K., & Bradley, B. P. (1999). Some methodological issues in "
        "assessing attentional biases. Behaviour Research and Therapy, 37(6), "
        "595-604.",
    ],
    "conditions": ["congruent", "incongruent"],
    "condition_balance": "probe-behind-threat / neutral 50/50; threat top/bottom 50/50",
    "task": "Press UP/DOWN for the probe's location (top or bottom).",
    "surface": {
        "units": "height", "background": "gray",
        "stim_pos": [0.0, 0.0], "top_pos": [0.0, 0.20], "bottom_pos": [0.0, -0.20],
        "stim_height": 0.08, "probe_char": ".", "probe_height": 0.12,
        "fixation_char": "+", "fixation_height": 0.05,
    },
    "timing": {"fixation_sec": 0.5, "stim_sec": 0.5, "max_response_sec": 2.0,
               "iti_sec": 0.5},
    "responses": {"mapping": {"top": "up", "bottom": "down"}, "quit_key": "escape",
                  "note": "Original used words in a vertical layout; modern "
                          "variants use faces in a horizontal layout."},
    "threat_words": ["DANGER", "CANCER", "FAILURE", "ATTACK", "DEATH"],
    "neutral_words": ["LEAGUE", "GARDEN", "FACTORY", "WINDOW", "BOTTLE"],
    "dv": ["probe-detection RT",
           "bias = RT(incongruent) - RT(congruent); positive = vigilance"],
}


def build_trials(reps: int = 12, seed: int = 0) -> list[dict]:
    rng = random.Random(seed)
    S, T = SPEC["surface"], SPEC["timing"]
    m = SPEC["responses"]["mapping"]
    pos_of = {"top": S["top_pos"], "bottom": S["bottom_pos"]}

    trials = []
    for _ in range(reps):
        for threat_pos in ("top", "bottom"):
            for probe_pos in ("top", "bottom"):
                neutral_pos = "bottom" if threat_pos == "top" else "top"
                tw = rng.choice(SPEC["threat_words"])
                nw = rng.choice(SPEC["neutral_words"])
                pair = [
                    text(tw, color="white", pos=pos_of[threat_pos], height=S["stim_height"]),
                    text(nw, color="white", pos=pos_of[neutral_pos], height=S["stim_height"]),
                ]
                probe = text(S["probe_char"], color="white", pos=pos_of[probe_pos],
                             height=S["probe_height"])
                cond = "congruent" if probe_pos == threat_pos else "incongruent"
                trials.append({
                    "condition": cond,
                    "phases": [
                        fixation_phase(SPEC),
                        phase([fixation(SPEC)] + pair, dur=T["stim_sec"]),
                        phase([probe], dur=T["max_response_sec"], collect=True,
                              keys=["up", "down"]),
                    ],
                    "correct_key": m[probe_pos],
                    "rt_phase": 2,
                    "meta": {"threat_pos": threat_pos, "probe_pos": probe_pos,
                             "threat_word": tw, "neutral_word": nw},
                })
    rng.shuffle(trials)
    return trials
