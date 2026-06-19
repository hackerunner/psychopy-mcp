"""{{NAME}} — PsychoPy Coder experiment scaffold.

Edit the trial list and routine below, then:
  validate_script("{{NAME}}.py")    # static check
  run_experiment("{{NAME}}.py")     # run it (a window opens) and collect data

Data is written to ./data/ as CSV (one row per trial).
"""
import os
from psychopy import visual, core, event, data, gui

# ── session info ──────────────────────────────────────────────
exp_info = {"participant": "001", "session": "01"}
dlg = gui.DlgFromDict(exp_info, title="{{NAME}}")
if not dlg.OK:
    core.quit()

os.makedirs("data", exist_ok=True)
filename = os.path.join(
    "data", f"{exp_info['participant']}_{{NAME}}_{data.getDateStr()}"
)

# ── window ────────────────────────────────────────────────────
win = visual.Window(size=[1024, 768], color="black", units="height", fullscr=False)

# ── stimuli ───────────────────────────────────────────────────
fixation = visual.TextStim(win, text="+", height=0.1, color="white")
stimulus = visual.TextStim(win, text="", height=0.15, color="white")
instructions = visual.TextStim(
    win, text="Press LEFT for red, RIGHT for blue.\n\nPress space to begin.",
    height=0.06, color="white", wrapWidth=1.2,
)

# ── trials: edit this list (or load from a conditions file) ───
trial_list = [
    {"word": "RED", "correct": "left"},
    {"word": "BLUE", "correct": "right"},
    {"word": "RED", "correct": "left"},
    {"word": "BLUE", "correct": "right"},
]
trials = data.TrialHandler(trial_list, nReps=2, method="random")
exp = data.ExperimentHandler(name="{{NAME}}", extraInfo=exp_info,
                             dataFileName=filename)
exp.addLoop(trials)

# ── instructions ──────────────────────────────────────────────
instructions.draw()
win.flip()
event.waitKeys(keyList=["space"])

# ── trial loop ────────────────────────────────────────────────
clock = core.Clock()
for trial in trials:
    fixation.draw()
    win.flip()
    core.wait(0.5)

    stimulus.text = trial["word"]
    stimulus.draw()
    win.flip()
    clock.reset()
    keys = event.waitKeys(keyList=["left", "right", "escape"], timeStamped=clock)
    key, rt = keys[0]
    if key == "escape":
        break
    trials.addData("response", key)
    trials.addData("rt", rt)
    trials.addData("correct", int(key == trial["correct"]))
    exp.nextEntry()

# ── save & quit ───────────────────────────────────────────────
exp.saveAsWideText(filename + ".csv")
win.close()
core.quit()
