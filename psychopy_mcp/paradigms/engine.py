"""Generic phase-based PsychoPy runtime for literature-grounded paradigms.

Every paradigm is expressed as a list of *trials*, and every trial as an
ordered list of *phases*. A phase draws a set of stimulus descriptors, holds
them for a fixed duration OR until a response, and optionally collects a
keypress. This single player covers Stroop, Flanker, Simon, Go/No-Go, Posner,
ANT, N-back, Sternberg, visual search, task-switching, lexical decision,
dot-probe and mental rotation.

Why a shared engine: surface parameters (window, background, font size, fixed
positions) come from ONE place per paradigm, so conditions cannot silently
diverge in size/position — the exact failure mode that hand-built, NL-generated
experiments fall into.

Trial schema (plain dicts, JSON-serialisable except for nested floats):
    {
      "condition": str,
      "phases": [ {phase}, ... ],
      "correct_key": str | None,         # for accuracy scoring (None = no scoring)
      "rt_phase": int,                   # index of the phase whose key/rt is the trial's response
      "meta": {col: value, ...},         # extra columns to log
    }
Phase schema:
    {
      "stims": [ {stim}, ... ],          # drawn together; [] = blank screen
      "dur": float | None,               # seconds; None = until response (response phase only)
      "collect": bool,                   # collect a keypress this phase
      "keys": [str, ...] | None,         # allowed keys (None = any)
    }
Stim descriptor (kind dispatches to a PsychoPy class):
    text   : {kind, text, color, pos, height, bold?, font?, ori?}
    rect   : {kind, pos, size:[w,h], lineColor?, fillColor?, ori?}
    circle : {kind, pos, radius, lineColor?, fillColor?}
    line   : {kind, start, end, color?}
    polygon: {kind, pos, radius, edges, lineColor?, fillColor?, ori?}
    image  : {kind, image, pos, size?}
"""
from __future__ import annotations

import os
from typing import Any, Optional


def _make_stim(win, visual, d: dict):
    kind = d.get("kind", "text")
    if kind == "text":
        return visual.TextStim(
            win, text=d.get("text", ""), color=d.get("color", "white"),
            pos=d.get("pos", [0, 0]), height=d.get("height", 0.1),
            bold=d.get("bold", False), font=d.get("font", "Arial"),
            ori=d.get("ori", 0.0), wrapWidth=d.get("wrapWidth", 2.0),
            flipHoriz=d.get("flipHoriz", False),
        )
    if kind == "rect":
        w, h = d.get("size", [0.2, 0.2])
        return visual.Rect(win, width=w, height=h, pos=d.get("pos", [0, 0]),
                           lineColor=d.get("lineColor", "white"),
                           fillColor=d.get("fillColor", None), ori=d.get("ori", 0.0))
    if kind == "circle":
        return visual.Circle(win, radius=d.get("radius", 0.1), pos=d.get("pos", [0, 0]),
                             lineColor=d.get("lineColor", "white"),
                             fillColor=d.get("fillColor", None), edges=64)
    if kind == "line":
        return visual.Line(win, start=d.get("start", [-0.1, 0]), end=d.get("end", [0.1, 0]),
                           lineColor=d.get("color", "white"))
    if kind == "polygon":
        return visual.Polygon(win, edges=d.get("edges", 5), radius=d.get("radius", 0.1),
                              pos=d.get("pos", [0, 0]), lineColor=d.get("lineColor", "white"),
                              fillColor=d.get("fillColor", None), ori=d.get("ori", 0.0))
    if kind == "image":
        return visual.ImageStim(win, image=d.get("image"), pos=d.get("pos", [0, 0]),
                                size=d.get("size"))
    raise ValueError(f"unknown stim kind: {kind}")


def run(spec: dict, trials: list[dict], exp_name: str,
        info: Optional[dict] = None, fullscr: bool = False,
        data_dir: str = "data", show_instructions: bool = True) -> str:
    """Run a paradigm and return the path to the saved CSV.

    Args:
        spec: the paradigm spec (uses spec["surface"], spec["timing"], spec["task"]).
        trials: list of trial dicts (see module docstring).
        exp_name: name used for the data filename and ExperimentHandler.
        info: extra experiment info to store (e.g. participant); shown as columns.
        fullscr: open the window fullscreen.
        data_dir: folder (created if needed) for the CSV/psydat output.
    """
    from psychopy import visual, core, event, data, gui

    info = dict(info or {})
    if not info:
        info = {"participant": "001", "session": "01"}
        if not gui.DlgFromDict(info, title=exp_name).OK:
            core.quit()

    os.makedirs(data_dir, exist_ok=True)
    fname = os.path.join(data_dir, f"{info.get('participant','001')}_{exp_name}_{data.getDateStr()}")

    S = spec["surface"]
    win = visual.Window(size=[1024, 768], color=S.get("background", "black"),
                        units=S.get("units", "height"), fullscr=fullscr, allowGUI=True)

    quit_key = spec.get("responses", {}).get("quit_key", "escape")

    exp = data.ExperimentHandler(name=exp_name, extraInfo=info, dataFileName=fname)
    handler = data.TrialHandler(trials, nReps=1, method="sequential")
    exp.addLoop(handler)

    # ── instructions ───────────────────────────────────────────
    if show_instructions:
        msg = spec.get("task", "Press the keys as instructed.")
        mapping = spec.get("responses", {}).get("mapping", {})
        keys_txt = "   ".join(f"{k}->{v}" for k, v in mapping.items())
        visual.TextStim(win, height=0.045, color="white", wrapWidth=1.5,
                        text=f"{msg}\n\n{keys_txt}\n\nPress SPACE to begin.").draw()
        win.flip()
        if event.waitKeys(keyList=["space", quit_key]) == [quit_key]:
            win.close(); core.quit()

    clock = core.Clock()
    aborted = False
    for trial in handler:
        resp_key, resp_rt = None, None
        rt_phase = trial.get("rt_phase", len(trial["phases"]) - 1)
        for i, phase in enumerate(trial["phases"]):
            for d in phase.get("stims", []):
                _make_stim(win, visual, d).draw()
            win.flip()
            if phase.get("collect"):
                keys = phase.get("keys")
                clock.reset()
                pressed = event.waitKeys(
                    maxWait=phase["dur"] if phase.get("dur") is not None else float("inf"),
                    keyList=(list(keys) + [quit_key]) if keys else None,
                    timeStamped=clock,
                )
                if pressed:
                    k, rt = pressed[0]
                    if k == quit_key:
                        aborted = True
                        break
                    if i == rt_phase:
                        resp_key, resp_rt = k, rt
            else:
                if phase.get("dur"):
                    core.wait(phase["dur"])
                # allow quitting during non-collect phases
                if event.getKeys(keyList=[quit_key]):
                    aborted = True
                    break
        if aborted:
            break

        correct = None
        if "correct_key" in trial:
            # correct_key=None means the correct action is to withhold (Go/No-Go)
            correct = int(resp_key == trial["correct_key"])
        handler.addData("condition", trial.get("condition"))
        handler.addData("response", resp_key)
        handler.addData("rt", resp_rt)
        if correct is not None:
            handler.addData("correct", correct)
        for col, val in trial.get("meta", {}).items():
            handler.addData(col, val)
        exp.nextEntry()

        iti = spec.get("timing", {}).get("iti_sec", 0.0)
        if iti:
            win.flip(); core.wait(iti)

    out_csv = fname + ".csv"
    exp.saveAsWideText(out_csv)
    print("SAVED:", out_csv, flush=True)
    win.close()
    core.quit()
    return out_csv
