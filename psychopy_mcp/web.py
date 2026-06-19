"""Export a paradigm to a Builder .psyexp + PsychoJS .js for online studies.

Only Builder (.psyexp) experiments auto-transpile to JavaScript (PsychoJS) and
run online on Pavlovia; pure Coder scripts do not. This module turns a paradigm
into a Builder experiment (instructions + fixation + stimulus + keyboard, looped
over a generated conditions CSV) and compiles it to .js.

Scope: paradigms whose response trial shows a single TEXT stimulus and collects
a keypress (Stroop, Flanker, Lexical Decision, and text-based custom paradigms).
Multi-stimulus / shape / multi-phase paradigms (Posner, ANT, Sternberg, visual
search, Simon, Go/No-Go, dot-probe, mental rotation) stay desktop-only for now
and return a clear message.
"""
from __future__ import annotations

import csv
from pathlib import Path

from psychopy_mcp import paradigms


def _extract_conditions(key: str, opts: dict):
    """Pull (word, ink, corrAns, condition) rows from a single-text paradigm.

    Returns (rows, allowed_keys) or raises ValueError if not web-exportable.
    """
    spec = paradigms.get_paradigm(key)
    if not spec:
        raise ValueError(f"unknown paradigm: {key}")
    trials = paradigms.build_trials(key, **(opts or {}))
    fix_char = spec.get("surface", {}).get("fixation_char", "+")
    rows = []
    for t in trials:
        rt_phase = t.get("rt_phase", len(t["phases"]) - 1)
        stims = t["phases"][rt_phase].get("stims", [])
        # the real stimulus is a text that is NOT the fixation marker, and there
        # must be no non-text stimuli (shapes/images) competing with it.
        non_text = [s for s in stims if s.get("kind") != "text"]
        texts = [s for s in stims
                 if s.get("kind") == "text" and s.get("text") != fix_char]
        if len(texts) != 1 or non_text:
            raise ValueError(
                f"'{key}' is not web-exportable yet: its response screen has "
                f"{len(texts)} non-fixation text stimuli and {len(non_text)} "
                f"shape/image stimuli (need exactly 1 text, 0 shapes). "
                f"Multi-stimulus / shape / multi-phase paradigms are "
                f"desktop-only for now.")
        s = texts[0]
        rows.append({
            "word": s.get("text", ""),
            "ink": s.get("color", "white"),
            "corrAns": t.get("correct_key", "") or "",
            "condition": t.get("condition", ""),
        })
    keys = list(spec.get("responses", {}).get("mapping", {}).values())
    return rows, keys, spec


def export(key: str, exp_name: str, out_dir: str) -> dict:
    from psychopy import experiment
    from psychopy.experiment.routines import Routine
    from psychopy.experiment.loops import TrialHandler

    key = key.lower()
    rows, keys, spec = _extract_conditions(key, {})
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # 1) conditions file
    cond_csv = out / f"{exp_name}_conditions.csv"
    with cond_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["word", "ink", "corrAns", "condition"])
        w.writeheader()
        w.writerows(rows)

    S, T = spec["surface"], spec["timing"]
    fix_h = S.get("fixation_height", 0.08)
    stim_h = S.get("stim_height", 0.1)
    fix_sec = T.get("fixation_sec", 0.5)
    max_rt = T.get("max_response_sec", "")
    allowed = ",".join(f"'{k}'" for k in keys)
    comps = experiment.getAllComponents()

    exp = experiment.Experiment()
    exp.settings.params["Units"].val = S.get("units", "height")
    exp.settings.params["expName"].val = exp_name
    exp.settings.params["Window size (pixels)"].val = "[1024, 768]"
    exp.settings.params["color"].val = S.get("background", "black")
    # the PsychoPy default participant field is a Python f-string that does NOT
    # transpile to JS; use a plain default so the online experiment is valid JS.
    if "Experiment info" in exp.settings.params:
        exp.settings.params["Experiment info"].val = (
            "{'participant':'001', 'session':'001'}")
    # the default Data filename uses Python %-formatting that isn't valid JS;
    # use string concatenation that works in both Python and JS.
    if "Data filename" in exp.settings.params:
        exp.settings.params["Data filename"].val = (
            "'data/' + expInfo['participant'] + '_' + expName")

    # instructions routine
    instr = Routine("instructions", exp)
    itxt = comps["TextComponent"](exp, "instructions", name="instrText",
                                  text=spec.get("task", "Respond as instructed.") +
                                  "\n\nPress SPACE to begin.",
                                  letterHeight=0.05, stopVal="")
    ikey = comps["KeyboardComponent"](exp, "instructions", name="instrKey",
                                      allowedKeys="'space'", forceEndRoutine=True,
                                      stopVal="")
    instr.addComponent(itxt)
    instr.addComponent(ikey)

    # trial routine: fixation -> stimulus + keyboard
    trial = Routine("trial", exp)
    fix = comps["TextComponent"](exp, "trial", name="fixation", text="+",
                                 letterHeight=fix_h, startVal=0.0,
                                 stopType="duration (s)", stopVal=fix_sec)
    stim = comps["TextComponent"](exp, "trial", name="stim", text="$word",
                                  color="$ink", letterHeight=stim_h,
                                  startVal=fix_sec, stopType="duration (s)",
                                  stopVal=max_rt)
    stim.params["text"].updates = "set every repeat"
    stim.params["color"].updates = "set every repeat"
    resp = comps["KeyboardComponent"](exp, "trial", name="resp",
                                      allowedKeys=allowed, correctAns="$corrAns",
                                      storeCorrect=True, forceEndRoutine=True,
                                      startVal=fix_sec, stopVal=max_rt)
    resp.params["correctAns"].updates = "set every repeat"
    trial.addComponent(fix)
    trial.addComponent(stim)
    trial.addComponent(resp)

    # flow: instructions, then trial looped over the conditions file
    exp.addRoutine("instructions", instr)
    exp.addRoutine("trial", trial)
    exp.flow.addRoutine(instr, 0)
    exp.flow.addRoutine(trial, 1)
    loop = TrialHandler(exp, name="trials", loopType="random", nReps=1,
                        conditionsFile=cond_csv.name)
    exp.flow.addLoop(loop, startPos=1, endPos=2)

    psyexp = out / f"{exp_name}.psyexp"
    exp.saveToXML(str(psyexp))

    # 2) compile to PsychoJS JavaScript
    js = out / f"{exp_name}.js"
    js_ok, js_err = True, ""
    try:
        from psychopy.scripts.psyexpCompile import compileScript
        compileScript(infile=str(psyexp), outfile=str(js))
    except Exception as e:
        js_ok, js_err = False, repr(e)

    return {
        "psyexp": str(psyexp),
        "conditions": str(cond_csv),
        "n_conditions": len(rows),
        "js": str(js) if js_ok else None,
        "js_error": js_err or None,
        "next": "Upload the folder to Pavlovia (pavlovia.org) or sync from the "
                "PsychoPy Builder to run online.",
    }
