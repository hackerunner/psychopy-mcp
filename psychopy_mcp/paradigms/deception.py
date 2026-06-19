"""Sheffield Lie Test / Differentiation of Deception (Spence 2001; Suchotzki 2017).

Each yes/no question is answered both truthfully and deceptively, cued by the
colour of the question text (green = tell the truth, red = lie / answer the
opposite). Lying is reliably slower and more error-prone than truth-telling
(the "lie effect"; meta-analytic d ~ 1.05). Because every question serves as its
own control, lie and truth trials are matched on content.

Questions have objective answers so the engine can score responses without
knowing anything private about the participant.
"""
from __future__ import annotations

import random

from .base import fixation_phase, response_phase, text

SPEC = {
    "name": "Sheffield Lie Test (Deception)",
    "summary": ("Answer yes/no questions truthfully or deceptively as cued by "
                "the question's colour. Lie effect = slower/less-accurate "
                "responding when lying than when telling the truth."),
    "references": [
        "Spence, S. A., Farrow, T. F. D., Herford, A. E., Wilkinson, I. D., "
        "Zheng, Y., & Woodruff, P. W. R. (2001). Behavioural and functional "
        "anatomical correlates of deception in humans. NeuroReport, 12(13), "
        "2849-2853.",
        "Suchotzki, K., Verschuere, B., Van Bockstaele, B., Ben-Shakhar, G., & "
        "Crombez, G. (2017). Lying takes time: A meta-analysis on reaction time "
        "measures of deception. Psychological Bulletin, 143(4), 428-453.",
    ],
    "conditions": ["truth", "lie"],
    "condition_balance": "equal; each question answered both truthfully and deceptively",
    "task": ("Answer each yes/no question. GREEN question = tell the TRUTH. "
             "RED question = LIE (give the wrong answer). yes = J, no = F."),
    "instructions": (
        "DECEPTION TASK\n"
        "\n"
        "You will see yes / no questions, one at a time.\n"
        "The COLOUR of the question tells you how to answer:\n"
        "\n"
        "    GREEN question   ->   tell the TRUTH\n"
        "    RED question     ->   LIE (give the WRONG answer)\n"
        "\n"
        "Respond with the keys:    J = yes      F = no\n"
        "\n"
        "Examples:\n"
        "    GREEN  'Is the sky blue?'   ->  truth ->  press J (yes)\n"
        "    RED    'Is the sky blue?'   ->  lie   ->  press F (no)\n"
        "    RED    'Do cats bark?'      ->  lie   ->  press J (yes)\n"
        "\n"
        "First there is a '+' to fixate on, then the question appears.\n"
        "Answer as quickly and accurately as you can.\n"
        "(Press ESC at any time to quit.)"
    ),
    "surface": {
        "units": "height", "background": "black",
        "stim_pos": [0.0, 0.0], "stim_height": 0.06,
        "truth_color": "lime", "lie_color": "red",
        "fixation_char": "+", "fixation_height": 0.08,
    },
    "timing": {"fixation_sec": 0.5, "max_response_sec": 5.0, "iti_sec": 1.0},
    "responses": {
        "mapping": {"yes": "j", "no": "f"}, "quit_key": "escape",
        "note": "Colour of the question text is the lie/truth cue.",
    },
    # yes/no questions with objective answers (6 'yes' + 6 'no')
    "questions": [
        ("Is the sky blue?", "yes"),
        ("Do fish live in water?", "yes"),
        ("Is grass green?", "yes"),
        ("Is ice frozen water?", "yes"),
        ("Is China in Asia?", "yes"),
        ("Can birds fly?", "yes"),
        ("Is fire cold?", "no"),
        ("Do cats bark?", "no"),
        ("Is the sun a planet?", "no"),
        ("Can humans breathe underwater?", "no"),
        ("Is two plus two five?", "no"),
        ("Do cars run on water?", "no"),
    ],
    "dv": ["RT (correct trials)", "accuracy",
           "lie effect = RT(lie) - RT(truth)"],
}


def build_trials(reps: int = 3, seed: int = 0) -> list[dict]:
    rng = random.Random(seed)
    S = SPEC["surface"]
    mapping = SPEC["responses"]["mapping"]          # yes/no -> key
    keys = list(mapping.values())
    opposite = {"yes": "no", "no": "yes"}

    trials = []
    for _ in range(reps):
        for (question, true_ans) in SPEC["questions"]:
            for cue in ("truth", "lie"):
                color = S["truth_color"] if cue == "truth" else S["lie_color"]
                answer = true_ans if cue == "truth" else opposite[true_ans]
                stim = text(question, color=color, pos=S["stim_pos"],
                            height=S["stim_height"])
                trials.append({
                    "condition": cue,
                    "phases": [fixation_phase(SPEC),
                               response_phase([stim], SPEC, keys)],
                    "correct_key": mapping[answer],
                    "rt_phase": 1,
                    "meta": {"question": question, "cue": cue,
                             "true_answer": true_ans},
                })
    rng.shuffle(trials)
    return trials
