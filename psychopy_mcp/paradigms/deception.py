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
    "task": ("根据上方提示词作答：提示「请说真话」则按正确答案，"
             "提示「请说谎」则按相反答案。J=是，F=否。"),
    "instructions": [
        # 第 1 页：欢迎 + 总览
        "说谎实验\n"
        "\n"
        "欢迎参加本实验，感谢你的参与。\n"
        "\n"
        "实验中，屏幕中央会逐个出现「是 / 否」问题，\n"
        "问题上方会有一个提示词，告诉你这一题该怎么回答。\n"
        "\n"
        "请坐姿舒适，将左右手食指分别放在 F 键和 J 键上。",
        # 第 2 页：规则 + 按键 + 例子
        "答题规则\n"
        "\n"
        "    提示「请说真话」(蓝色) →  按正确的答案\n"
        "    提示「请说谎」　(橙色) →  按相反的错误答案\n"
        "\n"
        "按键：    J 键 = 是　　　　F 键 = 否\n"
        "\n"
        "例子（问题：天空是蓝色的吗？）：\n"
        "    提示「请说真话」→ 真实答案是「是」→ 按 J\n"
        "    提示「请说谎」　→ 要答错 → 按 F（否）\n"
        "\n"
        "请尽量又快又准地作答。每题先出现「+」，再出现问题。\n"
        "（蓝/橙配色对红绿色盲友好，但请以提示词为准。）\n"
        "中途想退出，请按 ESC 键。",
    ],
    "surface": {
        "units": "height", "background": "black",
        "stim_pos": [0.0, 0.0], "stim_height": 0.08,
        "cue_pos": [0.0, 0.20], "cue_height": 0.06,
        # colour-blind-safe pair (Okabe-Ito): blue=truth, orange=lie. Colour is
        # only a REDUNDANT cue — the cue word below is the primary instruction,
        # so red-green (or any) colour-vision deficiency does not matter.
        "truth_color": "#0072B2", "lie_color": "#E69F00",
        "fixation_char": "+", "fixation_height": 0.08,
        "font": "Microsoft YaHei",            # CJK font for the questions
        "instruction_font": "Microsoft YaHei",  # CJK font for the instructions
    },
    "cue_labels": {"truth": "请说真话", "lie": "请说谎"},
    "begin_prompt": "按【空格键】开始实验",
    "continue_prompt": "按【空格键】继续",
    "timing": {"fixation_sec": 0.5, "max_response_sec": 5.0, "iti_sec": 1.0},
    "responses": {
        "mapping": {"yes": "j", "no": "f"}, "quit_key": "escape",
        "note": "Colour of the question text is the lie/truth cue.",
    },
    # 有客观答案的「是/否」问题（6 个"是" + 6 个"否"）
    "questions": [
        ("天空是蓝色的吗？", "yes"),
        ("鱼生活在水里吗？", "yes"),
        ("草是绿色的吗？", "yes"),
        ("冰是冻住的水吗？", "yes"),
        ("中国在亚洲吗？", "yes"),
        ("鸟会飞吗？", "yes"),
        ("火是冷的吗？", "no"),
        ("猫会汪汪叫吗？", "no"),
        ("太阳是一颗行星吗？", "no"),
        ("人能在水下呼吸吗？", "no"),
        ("二加二等于五吗？", "no"),
        ("汽车靠水行驶吗？", "no"),
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
                font = S.get("font", "Arial")
                # redundant cue: a coloured WORD (primary, accessible) above a
                # white question (so colour vision is never required).
                cue_stim = text(SPEC["cue_labels"][cue], color=color,
                                pos=S["cue_pos"], height=S["cue_height"], font=font)
                q_stim = text(question, color="white", pos=S["stim_pos"],
                              height=S["stim_height"], font=font)
                trials.append({
                    "condition": cue,
                    "phases": [fixation_phase(SPEC),
                               response_phase([cue_stim, q_stim], SPEC, keys)],
                    "correct_key": mapping[answer],
                    "rt_phase": 1,
                    "meta": {"question": question, "cue": cue,
                             "true_answer": true_ans},
                })
    rng.shuffle(trials)
    return trials
