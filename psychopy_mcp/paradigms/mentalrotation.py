"""Mental rotation task (Shepard & Metzler 1971; Cooper & Shepard 1973).

Uses the 2D alphanumeric variant (Cooper & Shepard 1973): an upright reference
character and a rotated comparison that is either the same or mirror-reversed.
RT increases linearly with rotation angle. (3D cube figures from Shepard &
Metzler 1971 require pre-rendered image assets; drop them in and switch the stim
to kind="image" to replicate the original exactly.)
"""
from __future__ import annotations

import random

from .base import fixation_phase, phase, text

SPEC = {
    "name": "Mental Rotation",
    "summary": ("Judge whether a rotated character is the same as an upright "
                "reference or its mirror image. RT increases linearly with the "
                "rotation angle."),
    "references": [
        "Shepard, R. N., & Metzler, J. (1971). Mental rotation of three-"
        "dimensional objects. Science, 171(3972), 701-703.",
        "Cooper, L. A., & Shepard, R. N. (1973). Chronometric studies of the "
        "rotation of mental images. In Visual Information Processing.",
    ],
    "conditions": ["angle_0", "angle_50", "angle_100", "angle_150"],
    "condition_balance": "same/mirror 50/50; angle balanced across same & mirror",
    "task": "Are the two characters the same (rotated) or MIRROR images?",
    "surface": {
        "units": "height", "background": "white",
        "stim_pos": [0.0, 0.0], "ref_pos": [-0.22, 0.0], "cmp_pos": [0.22, 0.0],
        "stim_height": 0.30, "stim_char": "R", "stim_color": "black",
        "angles_deg": [0, 50, 100, 150], "fixation_char": "+", "fixation_height": 0.05,
    },
    "timing": {"fixation_sec": 0.5, "max_response_sec": 10.0, "iti_sec": 1.0},
    "responses": {"mapping": {"same": "f", "mirror": "j"}, "quit_key": "escape",
                  "note": "Counterbalance hand-response mapping across subjects."},
    "dv": ["RT for correct 'same' responses",
           "RT linear with angle; slope ~ rotation rate (~60 deg/s)"],
}


def build_trials(reps: int = 10, seed: int = 0) -> list[dict]:
    rng = random.Random(seed)
    S = SPEC["surface"]
    m = SPEC["responses"]["mapping"]
    keys = list(m.values())
    ch, col, h = S["stim_char"], S["stim_color"], S["stim_height"]

    trials = []
    for _ in range(reps):
        for angle in S["angles_deg"]:
            for kind in ("same", "mirror"):
                ref = text(ch, color=col, pos=S["ref_pos"], height=h)
                cmp = text(ch, color=col, pos=S["cmp_pos"], height=h,
                           ori=angle, flipHoriz=(kind == "mirror"))
                trials.append({
                    "condition": f"angle_{angle}",
                    "phases": [fixation_phase(SPEC),
                               phase([ref, cmp],
                                     dur=SPEC["timing"]["max_response_sec"],
                                     collect=True, keys=keys)],
                    "correct_key": m[kind],
                    "rt_phase": 1,
                    "meta": {"angle": angle, "pair_type": kind},
                })
    rng.shuffle(trials)
    return trials
