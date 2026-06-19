"""Lexical Decision task (Meyer & Schvaneveldt 1971; Ratcliff et al. 2004)."""
from __future__ import annotations

import random

from .base import fixation_phase, response_phase, text

SPEC = {
    "name": "Lexical Decision Task",
    "summary": ("Decide whether a letter string is a real word or a non-word. "
                "Lexicality effect = nonword RT - word RT; word-frequency "
                "effect = low- minus high-frequency word RT."),
    "references": [
        "Meyer, D. E., & Schvaneveldt, R. W. (1971). Facilitation in recognizing "
        "pairs of words. Journal of Experimental Psychology, 90(2), 227-234.",
        "Ratcliff, R., Gomez, P., & McKoon, G. (2004). A diffusion model account "
        "of the lexical decision task. Psychological Review, 111(1), 159-182.",
    ],
    "conditions": ["word_high", "word_low", "nonword"],
    "condition_balance": "50% words / 50% nonwords; words split high/low frequency",
    "task": "Is the string a real WORD or a NON-WORD?",
    "surface": {
        "units": "height", "background": "gray",
        "stim_pos": [0.0, 0.0], "stim_height": 0.08, "font": "Consolas",
        "text_color": "black", "fixation_char": "+", "fixation_height": 0.05,
    },
    "timing": {"fixation_sec": 0.5, "max_response_sec": 2.0, "iti_sec": 0.5},
    "responses": {
        "mapping": {"word": "m", "nonword": "z"}, "quit_key": "escape",
        "note": "Counterbalance which key = word across participants. Use "
                "pronounceable, length-matched pseudowords (Ratcliff 2004).",
    },
    # small built-in length-matched sets; replace with ELP/SUBTLEX for studies
    "words_high": ["TIME", "YEAR", "PEOPLE", "WATER", "HOUSE", "WORLD"],
    "words_low": ["MOAT", "LUTE", "FERRET", "QUILT", "GROTTO", "BRINK"],
    "nonwords": ["BLANT", "CRELP", "FOMBLE", "TRINK", "PLORE", "DRAPE"],
    "dv": ["RT (correct)", "accuracy",
           "lexicality effect = nonword RT - word RT"],
}


def build_trials(reps: int = 8, seed: int = 0) -> list[dict]:
    rng = random.Random(seed)
    S = SPEC["surface"]
    m = SPEC["responses"]["mapping"]
    keys = list(m.values())

    items = ([(w, "word_high", m["word"]) for w in SPEC["words_high"]] +
             [(w, "word_low", m["word"]) for w in SPEC["words_low"]] +
             [(w, "nonword", m["nonword"]) for w in SPEC["nonwords"]])

    trials = []
    for _ in range(reps):
        for (string, cond, ckey) in items:
            stim = text(string, color=S["text_color"], pos=S["stim_pos"],
                        height=S["stim_height"], font=S["font"])
            trials.append({
                "condition": cond,
                "phases": [fixation_phase(SPEC), response_phase([stim], SPEC, keys)],
                "correct_key": ckey,
                "rt_phase": 1,
                "meta": {"string": string},
            })
    rng.shuffle(trials)
    return trials
