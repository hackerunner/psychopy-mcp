"""Simon task (Simon & Rudell 1967)."""
from __future__ import annotations

import random

from .base import circle, fixation, fixation_phase, phase, response_phase

SPEC = {
    "name": "Simon Task",
    "summary": ("Respond by colour with a left/right key while the stimulus "
                "appears left or right (irrelevant). Simon effect = faster when "
                "stimulus side matches the response side."),
    "references": [
        "Simon, J. R., & Rudell, A. P. (1967). Auditory S-R compatibility: The "
        "effect of an irrelevant cue on information processing. Journal of "
        "Applied Psychology, 51(3), 300-304.",
        "Hommel, B. (2011). The Simon effect as tool and heuristic. Acta "
        "Psychologica, 136(2), 189-202.",
    ],
    "conditions": ["congruent", "incongruent"],
    "condition_balance": "equal; colour x location fully crossed and equiprobable",
    "task": "Press the key for the COLOUR; ignore where it appears.",
    "surface": {
        "units": "height", "background": "white",
        "stim_pos": [0.0, 0.0], "stim_left": [-0.25, 0.0], "stim_right": [0.25, 0.0],
        "stim_radius": 0.06, "fixation_char": "+", "fixation_height": 0.05,
    },
    "timing": {"fixation_sec": 0.5, "max_response_sec": 1.0, "iti_sec": 0.5},
    "responses": {
        "mapping": {"red": "f", "green": "j"},
        "quit_key": "escape",
        "note": "Counterbalance colour-key mapping across participants.",
    },
    "colors": ["red", "green"],
    "dv": ["RT (correct)", "accuracy",
           "Simon effect = RT(incongruent) - RT(congruent)"],
}

_SIDE = {"f": "left", "j": "right"}  # which key is on which side


def build_trials(reps: int = 40, seed: int = 0) -> list[dict]:
    rng = random.Random(seed)
    S = SPEC["surface"]
    mapping = SPEC["responses"]["mapping"]            # colour -> key
    keys = list(mapping.values())
    pos_of = {"left": S["stim_left"], "right": S["stim_right"]}

    combos = []  # (colour, location)
    for colour in SPEC["colors"]:
        for loc in ("left", "right"):
            combos.append((colour, loc))

    trials = []
    for _ in range(reps):
        for (colour, loc) in combos:
            key = mapping[colour]
            resp_side = _SIDE[key]
            cond = "congruent" if resp_side == loc else "incongruent"
            stim = circle(pos=pos_of[loc], radius=S["stim_radius"], fillColor=colour,
                          lineColor=colour)
            trials.append({
                "condition": cond,
                "phases": [fixation_phase(SPEC),
                           phase([fixation(SPEC), stim],
                                 dur=SPEC["timing"]["max_response_sec"],
                                 collect=True, keys=keys)],
                "correct_key": key,
                "rt_phase": 1,
                "meta": {"color": colour, "location": loc},
            })
    rng.shuffle(trials)
    return trials
