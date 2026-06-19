"""N-back working memory task (Kirchner 1958; Owen et al. 2005)."""
from __future__ import annotations

import random

from .base import fixation_phase, phase, text

SPEC = {
    "name": "N-back",
    "summary": ("Press when the current letter matches the one shown N items "
                "earlier. DV is accuracy/d-prime and RT to targets."),
    "references": [
        "Kirchner, W. K. (1958). Age differences in short-term retention of "
        "rapidly changing information. JEP, 55(4), 352-358.",
        "Owen, A. M., et al. (2005). N-back working memory paradigm: A "
        "meta-analysis of normative functional neuroimaging studies. Human "
        "Brain Mapping, 25(1), 46-59.",
    ],
    "conditions": ["1-back", "2-back", "3-back"],
    "condition_balance": "~33% targets (matches) per block",
    "task": "Press SPACE when the letter matches the one N letters back.",
    "surface": {
        "units": "height", "background": "gray",
        "stim_pos": [0.0, 0.0], "stim_height": 0.12, "stim_color": "white",
        "fixation_char": "+", "fixation_height": 0.05,
    },
    "timing": {"fixation_sec": 0.5, "stim_sec": 0.5, "isi_sec": 2.5,
               "max_response_sec": 2.5, "iti_sec": 0.0},
    "responses": {"mapping": {"match": "space"}, "quit_key": "escape",
                  "note": "Respond only to matches (target trials)."},
    "letters": list("BCDFGHJKLMNPQRSTV"),
    "dv": ["accuracy / d-prime (hits - false alarms)", "RT to matches"],
}


def build_trials(n: int = 2, total: int = 30, n_targets: int = 10,
                 seed: int = 0) -> list[dict]:
    rng = random.Random(seed)
    S, T = SPEC["surface"], SPEC["timing"]
    pool = SPEC["letters"]

    # choose target positions among indices [n, total)
    eligible = list(range(n, total))
    n_targets = min(n_targets, len(eligible))
    targets = set(rng.sample(eligible, n_targets))

    seq = []
    for i in range(total):
        if i in targets:
            seq.append(seq[i - n])                       # force a match
        else:
            choices = [c for c in pool if not (i >= n and c == seq[i - n])]
            seq.append(rng.choice(choices))              # avoid accidental match

    trials = []
    for i, letter in enumerate(seq):
        is_target = i in targets
        stim = text(letter, color=S["stim_color"], pos=S["stim_pos"],
                    height=S["stim_height"])
        trials.append({
            "condition": f"{n}-back",
            "phases": [fixation_phase(SPEC),
                       phase([stim], dur=T["max_response_sec"], collect=True,
                             keys=["space"])],
            "correct_key": "space" if is_target else None,
            "rt_phase": 1,
            "meta": {"letter": letter, "is_target": int(is_target), "pos": i},
        })
    return trials   # order matters for n-back; do NOT shuffle
