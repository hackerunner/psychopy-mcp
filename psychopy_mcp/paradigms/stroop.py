"""Colour-Word Stroop (Stroop 1935; MacLeod 1991)."""
from __future__ import annotations

import random

from .base import fixation_phase, response_phase, text

SPEC = {
    "name": "Colour-Word Stroop",
    "summary": ("Name the INK colour of a colour word; ink and meaning are "
                "congruent, incongruent, or neutral. Stroop effect = slower "
                "responding on incongruent vs congruent trials."),
    "references": [
        "Stroop, J. R. (1935). Studies of interference in serial verbal reactions. "
        "Journal of Experimental Psychology, 18(6), 643-662.",
        "MacLeod, C. M. (1991). Half a century of research on the Stroop effect: "
        "An integrative review. Psychological Bulletin, 109(2), 163-203.",
    ],
    "conditions": ["congruent", "incongruent", "neutral"],
    "condition_balance": "equal #congruent = #incongruent = #neutral (MacLeod 1991)",
    "task": "Name the INK COLOUR of the word, ignore what the word says.",
    "surface": {
        "units": "height", "background": "black",
        "stim_pos": [0.0, 0.0], "stim_height": 0.12, "fixation_char": "+",
        "fixation_height": 0.10,
    },
    "timing": {"fixation_sec": 0.5, "max_response_sec": 2.0, "iti_sec": 0.5},
    "responses": {
        "mapping": {"red": "r", "green": "g", "blue": "b", "yellow": "y"},
        "quit_key": "escape",
        "note": "Counterbalance colour-key mapping across participants.",
    },
    "colors": ["red", "green", "blue", "yellow"],
    "words": ["RED", "GREEN", "BLUE", "YELLOW"],
    "neutral_word": "XXXX",
    "dv": ["RT on correct trials", "accuracy",
           "Stroop effect = RT(incongruent) - RT(congruent)"],
}


def build_trials(reps: int = 4, seed: int = 0) -> list[dict]:
    rng = random.Random(seed)
    S, T = SPEC["surface"], SPEC["timing"]
    colors, words = SPEC["colors"], SPEC["words"]
    mapping = SPEC["responses"]["mapping"]
    keys = list(mapping.values())
    W = len(colors) - 1  # weight congruent/neutral so all conditions are equal

    combos = []
    for w in words:                                     # congruent (xW)
        ink = colors[words.index(w)]
        combos += W * [(w, ink, "congruent")]
    for w in words:                                     # incongruent (x1 each)
        for ink in [c for c in colors if c != colors[words.index(w)]]:
            combos.append((w, ink, "incongruent"))
    for ink in colors:                                  # neutral (xW)
        combos += W * [(SPEC["neutral_word"], ink, "neutral")]

    trials = []
    for _ in range(reps):
        for (word, ink, cond) in combos:
            stim = text(word, color=ink, pos=S["stim_pos"],
                        height=S["stim_height"], bold=True)
            trials.append({
                "condition": cond,
                "phases": [fixation_phase(SPEC), response_phase([stim], SPEC, keys)],
                "correct_key": mapping[ink],
                "rt_phase": 1,
                "meta": {"word": word, "ink": ink},
            })
    rng.shuffle(trials)
    return trials
