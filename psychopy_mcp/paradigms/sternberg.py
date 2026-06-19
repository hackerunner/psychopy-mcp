"""Sternberg memory-scanning task (Sternberg 1966)."""
from __future__ import annotations

import random

from .base import blank_phase, fixation_phase, phase, response_phase, text

SPEC = {
    "name": "Sternberg Memory Scanning",
    "summary": ("Memorise a short digit set, then decide whether a probe digit "
                "was in the set. RT increases ~linearly with set size "
                "(~38 ms/item)."),
    "references": [
        "Sternberg, S. (1966). High-speed scanning in human memory. Science, "
        "153(3736), 652-654.",
        "Sternberg, S. (1969). Memory-scanning: Mental processes revealed by "
        "reaction-time experiments. American Scientist, 57(4), 421-457.",
    ],
    "conditions": ["set1", "set2", "set4", "set6"],
    "condition_balance": "~50% positive / ~50% negative probes within each set size",
    "task": "Was the probe digit in the memorised set? Present or Absent.",
    "surface": {
        "units": "height", "background": "black",
        "stim_pos": [0.0, 0.0], "stim_height": 0.12, "stim_color": "white",
        "fixation_char": "+", "fixation_height": 0.05,
    },
    "timing": {"fixation_sec": 0.5, "stim_sec": 1.2, "retention_delay_sec": 2.0,
               "max_response_sec": 3.0, "iti_sec": 1.0},
    "responses": {"mapping": {"present": "m", "absent": "z"}, "quit_key": "escape",
                  "note": "stim_sec = per-item study duration."},
    "dv": ["mean RT by set size", "search slope (~38 ms/item)", "accuracy"],
}


def build_trials(set_sizes=(1, 2, 4, 6), reps: int = 5, seed: int = 0) -> list[dict]:
    rng = random.Random(seed)
    S, T = SPEC["surface"], SPEC["timing"]
    m = SPEC["responses"]["mapping"]
    keys = list(m.values())
    digits = [str(d) for d in range(10)]

    trials = []
    for _ in range(reps):
        for size in set_sizes:
            for probe_type in ("positive", "negative"):
                mem = rng.sample(digits, size)
                if probe_type == "positive":
                    probe = rng.choice(mem)
                    ckey = m["present"]
                else:
                    probe = rng.choice([d for d in digits if d not in mem])
                    ckey = m["absent"]
                study = [phase([text(d, color=S["stim_color"], pos=S["stim_pos"],
                                     height=S["stim_height"])], dur=T["stim_sec"])
                         for d in mem]
                probe_stim = text(probe + "?", color="yellow", pos=S["stim_pos"],
                                  height=S["stim_height"])
                phases = ([fixation_phase(SPEC)] + study +
                          [blank_phase(T["retention_delay_sec"]),
                           response_phase([probe_stim], SPEC, keys)])
                trials.append({
                    "condition": f"set{size}",
                    "phases": phases,
                    "correct_key": ckey,
                    "rt_phase": len(phases) - 1,
                    "meta": {"set_size": size, "probe": probe,
                             "probe_type": probe_type, "memset": "".join(mem)},
                })
    rng.shuffle(trials)
    return trials
