"""PsychoPy MCP server.

Runs inside the dedicated Python 3.10 venv that also has `psychopy` installed,
so it can introspect PsychoPy, compile Builder files, run experiments as
subprocesses, and drive a live (interactive) PsychoPy window.

Exposed tools (grouped):
  introspection : env_info, list_components, api_help
  authoring     : scaffold_experiment, validate_script
  execution     : run_experiment, list_data, read_data
  builder       : read_psyexp, compile_psyexp
  live control  : live_start, live_cmd, live_stop, live_status

Claude/Codex edit the experiment *.py* files with their own native file tools;
this server provides the PsychoPy-specific verbs (validate / run / compile /
introspect / drive a window) that those tools cannot do.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from psychopy_mcp.paths import (
    CUSTOM_DIR, LIVE_SCRIPT, TEMPLATES, VENV_PY, WORKSPACE,
)

WORKSPACE.mkdir(parents=True, exist_ok=True)

mcp = FastMCP("psychopy")


def _py() -> str:
    """Interpreter used to run experiments / live session (the psychopy venv)."""
    return str(VENV_PY) if VENV_PY.exists() else sys.executable


def _resolve(path: str) -> Path:
    """Resolve a user-supplied path against the workspace if it is relative."""
    p = Path(path)
    if not p.is_absolute():
        p = WORKSPACE / p
    return p


# ───────────────────────── introspection ─────────────────────────


@mcp.tool()
def env_info() -> dict:
    """Report the PsychoPy environment: interpreter, versions, install path.

    Call this first to confirm the MCP is wired to a working PsychoPy venv.
    """
    info: dict[str, Any] = {
        "server_python": sys.version,
        "experiment_python": _py(),
        "venv_exists": VENV_PY.exists(),
        "workspace": str(WORKSPACE),
    }
    try:
        import psychopy  # noqa

        info["psychopy_version"] = psychopy.__version__
        info["psychopy_path"] = str(Path(psychopy.__file__).parent)
        info["psychopy_importable"] = True
    except Exception as e:  # pragma: no cover
        info["psychopy_importable"] = False
        info["psychopy_error"] = repr(e)
    return info


@mcp.tool()
def list_components(query: str = "") -> dict:
    """List available PsychoPy visual stimulus classes and Builder components.

    Args:
        query: optional case-insensitive substring filter (e.g. "text", "grating").
    """
    out: dict[str, Any] = {"visual_stimuli": [], "builder_components": []}
    q = query.lower()
    try:
        import psychopy.visual as visual

        for name in dir(visual):
            obj = getattr(visual, name)
            if isinstance(obj, type) and name[0].isupper():
                if not q or q in name.lower():
                    out["visual_stimuli"].append(name)
    except Exception as e:
        out["visual_error"] = repr(e)
    try:
        from psychopy.experiment import getAllComponents

        comps = getAllComponents()
        out["builder_components"] = sorted(
            n for n in comps if not q or q in n.lower()
        )
    except Exception as e:
        out["builder_error"] = repr(e)
    return out


@mcp.tool()
def api_help(symbol: str) -> dict:
    """Return the signature and docstring for a PsychoPy symbol.

    Args:
        symbol: dotted path, e.g. "visual.TextStim", "core.wait", "event.waitKeys",
                or "visual.GratingStim.__init__".
    """
    import importlib
    import inspect

    parts = symbol.split(".")
    # try progressively shorter module prefixes
    for split in range(len(parts) - 1, 0, -1):
        mod_name = "psychopy." + ".".join(parts[:split])
        try:
            mod = importlib.import_module(mod_name)
        except Exception:
            continue
        obj: Any = mod
        try:
            for attr in parts[split:]:
                obj = getattr(obj, attr)
        except AttributeError:
            continue
        try:
            sig = str(inspect.signature(obj))
        except (TypeError, ValueError):
            sig = ""
        return {
            "symbol": symbol,
            "signature": (parts[-1] + sig) if sig else "",
            "doc": inspect.getdoc(obj) or "",
        }
    return {"symbol": symbol, "error": "could not resolve symbol under psychopy.*"}


# ───────────────────────── authoring ─────────────────────────


@mcp.tool()
def scaffold_experiment(name: str, kind: str = "coder") -> dict:
    """Create a starter experiment file in the workspace from a template.

    Args:
        name: experiment name (used for the filename, no extension).
        kind: "coder" for a runnable Python script, "builder" for a .psyexp stub.

    Returns the created path. Edit it afterwards with your normal file tools,
    then validate_script / run_experiment it.
    """
    safe = "".join(c for c in name if c.isalnum() or c in "-_").strip("-_") or "experiment"
    if kind == "builder":
        tpl = (TEMPLATES / "experiment.psyexp").read_text(encoding="utf-8")
        dest = WORKSPACE / f"{safe}.psyexp"
    else:
        tpl = (TEMPLATES / "coder_experiment.py").read_text(encoding="utf-8")
        dest = WORKSPACE / f"{safe}.py"
    if dest.exists():
        return {"error": f"{dest} already exists; choose another name"}
    dest.write_text(tpl.replace("{{NAME}}", safe), encoding="utf-8")
    return {"path": str(dest), "kind": kind}


@mcp.tool()
def list_paradigms() -> dict:
    """List built-in literature-grounded experiment paradigms.

    Each paradigm pins the canonical design + surface parameters (font size,
    centred position, timing) of a classic task, with citations, so generated
    experiments match prior research instead of using invented values. Use
    get_paradigm for the full spec, scaffold_paradigm to generate a script.
    """
    from psychopy_mcp import paradigms
    return {"paradigms": paradigms.list_paradigms()}


@mcp.tool()
def get_paradigm(key: str) -> dict:
    """Return the full literature-grounded spec for a paradigm.

    Includes the canonical design, fixed surface parameters (positions/sizes
    shared across all conditions), timing, response mapping, dependent
    variables, and references.

    Args:
        key: paradigm key from list_paradigms (e.g. "stroop").
    """
    from psychopy_mcp import paradigms
    spec = paradigms.get_paradigm(key)
    return spec if spec else {"error": f"unknown paradigm: {key}"}


@mcp.tool()
def scaffold_paradigm(key: str, name: str, opts: Optional[dict] = None) -> dict:
    """Generate a complete, literature-grounded experiment script in the workspace.

    Unlike scaffold_experiment (a blank template), this emits a runnable script
    whose parameters come from the paradigm spec — every condition shares the
    same font size and centred position by construction, so the common errors of
    NL-built experiments (inconsistent size/position) cannot occur. Edit it
    afterwards, then validate_script / run_experiment it.

    Args:
        key: paradigm key (e.g. "stroop"); see list_paradigms.
        name: experiment name (used for the filename, no extension).
        opts: optional generation options forwarded to the paradigm's
              build_trials (e.g. {"reps": 2} for stroop, {"n": 3} for nback).
    """
    from psychopy_mcp import paradigms
    if not paradigms.get_paradigm(key):
        return {"error": f"unknown paradigm: {key}; see list_paradigms"}
    safe = "".join(c for c in name if c.isalnum() or c in "-_").strip("-_") or key
    dest = WORKSPACE / f"{safe}.py"
    if dest.exists():
        return {"error": f"{dest} already exists; choose another name"}
    src = paradigms.generate_script(key, safe, opts or {})
    dest.write_text(src, encoding="utf-8")
    return {"path": str(dest), "paradigm": key, "opts": opts or {}}


@mcp.tool()
def create_custom_paradigm(
    name: str, items: list[dict], mapping: dict, reps: int = 10,
    summary: str = "", background: str = "black", stim_height: float = 0.12,
) -> dict:
    """Define a custom choice-RT paradigm and save it so it runs like a built-in.

    The custom paradigm runs on the same engine, so all items share the surface
    parameters. After creating it, it appears in list_paradigms and can be built
    with scaffold_paradigm.

    Args:
        name: paradigm name (also the key, slugified).
        items: list of {"text", "color"?, "condition"?, "correct_key"?} dicts;
               correct_key must be one of the mapping values (or omit for none).
        mapping: response mapping {label: key}, e.g. {"left": "f", "right": "j"}.
        reps: repetitions per item.
        summary: one-line description.
        background: window background colour.
        stim_height: stimulus font height (height units), shared by all items.
    """
    from psychopy_mcp import paradigms
    from psychopy_mcp.paradigms import custom as customlib
    spec = customlib.create_template(name)
    spec["summary"] = summary or f"Custom paradigm: {name}"
    spec["responses"]["mapping"] = mapping
    spec["surface"]["background"] = background
    spec["surface"]["stim_height"] = stim_height
    spec["items"] = items
    spec["reps"] = reps
    errs = customlib.validate(spec)
    if errs:
        return {"error": "invalid spec", "problems": errs}
    path = customlib.save(spec, paradigms.CUSTOM_DIR)
    return {"path": str(path), "key": path.stem, "items": len(items)}


@mcp.tool()
def validate_script(path: str) -> dict:
    """Statically check a PsychoPy script: syntax + that psychopy imports resolve.

    Compiles the file (catching SyntaxErrors) and runs an import-only pass in the
    psychopy venv WITHOUT executing the experiment (no window opens).

    Args:
        path: path to a .py file (relative paths resolve under the workspace).
    """
    p = _resolve(path)
    if not p.exists():
        return {"ok": False, "error": f"not found: {p}"}
    src = p.read_text(encoding="utf-8")
    try:
        compile(src, str(p), "exec")
    except SyntaxError as e:
        return {"ok": False, "stage": "syntax", "error": f"{e.msg} (line {e.lineno})"}
    # import-only check: load the module's imports without running the body
    checker = (
        "import ast,sys\n"
        "src=open(sys.argv[1],encoding='utf-8').read()\n"
        "tree=ast.parse(src)\n"
        "import importlib\n"
        "errs=[]\n"
        "for n in ast.walk(tree):\n"
        "  mods=[]\n"
        "  if isinstance(n,ast.Import): mods=[a.name for a in n.names]\n"
        "  elif isinstance(n,ast.ImportFrom) and n.level==0 and n.module: mods=[n.module]\n"
        "  for m in mods:\n"
        "    try: importlib.import_module(m)\n"
        "    except Exception as e: errs.append(f'{m}: {e!r}')\n"
        "print('\\n'.join(errs))\n"
    )
    try:
        r = subprocess.run(
            [_py(), "-c", checker, str(p)],
            capture_output=True, text=True, timeout=120,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "stage": "import", "error": "import check timed out"}
    import_errs = r.stdout.strip()
    if import_errs:
        return {"ok": False, "stage": "import", "error": import_errs}
    return {"ok": True, "message": "syntax + imports OK (not executed)"}


# ───────────────────────── execution ─────────────────────────


@mcp.tool()
def run_experiment(
    path: str, args: Optional[list[str]] = None, timeout: int = 600, cwd: str = ""
) -> dict:
    """Run a PsychoPy experiment script as a subprocess and capture results.

    A real window will open (PsychoPy is GUI-based; true headless is not supported
    on Windows). Captures stdout/stderr and lists data files created/modified
    during the run so you can inspect results with read_data.

    Args:
        path: .py experiment to run (relative resolves under workspace).
        args: extra CLI args passed to the script.
        timeout: seconds before the run is killed (default 600).
        cwd: working directory; defaults to the script's folder.
    """
    p = _resolve(path)
    if not p.exists():
        return {"error": f"not found: {p}"}
    work = Path(cwd) if cwd else p.parent
    data_dir = work / "data"
    before = _snapshot(work)
    cmd = [_py(), str(p)] + (args or [])
    t0 = time.time()
    try:
        r = subprocess.run(
            cmd, cwd=str(work), capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired as e:
        return {
            "ok": False, "timed_out": True, "timeout": timeout,
            "stdout": (e.stdout or "")[-4000:], "stderr": (e.stderr or "")[-4000:],
        }
    after = _snapshot(work)
    changed = sorted(
        str(f) for f, m in after.items() if before.get(f) != m
    )
    return {
        "ok": r.returncode == 0,
        "returncode": r.returncode,
        "elapsed_sec": round(time.time() - t0, 1),
        "stdout": r.stdout[-4000:],
        "stderr": r.stderr[-4000:],
        "data_files_changed": changed,
        "data_dir": str(data_dir),
    }


def _snapshot(root: Path) -> dict[str, float]:
    snap: dict[str, float] = {}
    for sub in ("data", "."):
        d = root / sub if sub != "." else root
        if not d.exists():
            continue
        for f in d.glob("*"):
            if f.is_file() and f.suffix.lower() in (
                ".csv", ".tsv", ".log", ".psydat", ".xlsx", ".json"
            ):
                try:
                    snap[str(f)] = f.stat().st_mtime
                except OSError:
                    pass
    return snap


@mcp.tool()
def list_data(folder: str = "") -> dict:
    """List PsychoPy data files (csv/tsv/log/psydat/xlsx) under a folder.

    Args:
        folder: defaults to workspace/data and workspace; relative resolves under workspace.
    """
    roots = [_resolve(folder)] if folder else [WORKSPACE, WORKSPACE / "data"]
    files = []
    for root in roots:
        if not root.exists():
            continue
        for f in root.rglob("*"):
            if f.is_file() and f.suffix.lower() in (
                ".csv", ".tsv", ".log", ".psydat", ".xlsx", ".json"
            ):
                st = f.stat()
                files.append({"path": str(f), "size": st.st_size, "mtime": st.st_mtime})
    files.sort(key=lambda x: x["mtime"], reverse=True)
    return {"files": files[:200]}


@mcp.tool()
def read_data(path: str, max_rows: int = 50) -> dict:
    """Read and summarize a PsychoPy data file.

    Handles .csv/.tsv (via pandas), .psydat (psychopy trial handlers), and .log
    (plain text). Returns columns, shape, and the first rows.

    Args:
        path: data file path (relative resolves under workspace).
        max_rows: max rows to include in the preview.
    """
    p = _resolve(path)
    if not p.exists():
        return {"error": f"not found: {p}"}
    suf = p.suffix.lower()
    if suf in (".csv", ".tsv", ".xlsx"):
        try:
            import pandas as pd

            df = pd.read_csv(p, sep="\t" if suf == ".tsv" else ",") if suf != ".xlsx" \
                else pd.read_excel(p)
            return {
                "kind": "table",
                "shape": list(df.shape),
                "columns": list(map(str, df.columns)),
                "rows": df.head(max_rows).to_dict(orient="records"),
            }
        except Exception as e:
            return {"error": repr(e)}
    if suf == ".psydat":
        try:
            from psychopy.misc import fromFile

            obj = fromFile(str(p))
            summary = {"kind": "psydat", "type": type(obj).__name__}
            for attr in ("extraInfo", "trialList"):
                if hasattr(obj, attr):
                    summary[attr] = getattr(obj, attr)
            return summary
        except Exception as e:
            return {"error": repr(e)}
    # log / text
    text = p.read_text(encoding="utf-8", errors="replace")
    return {"kind": "text", "preview": text[:8000]}


@mcp.tool()
def analyze_data(path: str, paradigm: str = "", plot: bool = True) -> dict:
    """Compute a paradigm's canonical effect from its data CSV (+ optional plot).

    Returns mean RT and accuracy per condition plus the paradigm-specific
    dependent variable: Stroop/flanker/Simon congruency effect, Posner validity
    effect, switch cost, search/Sternberg slope (ms/item), mental-rotation slope
    (ms/deg), N-back d-prime, ANT network scores, or Go/No-Go commission rate.
    Falls back to a generic per-condition summary for custom paradigms.

    Args:
        path: data CSV (relative resolves under workspace).
        paradigm: paradigm key (e.g. "stroop"); inferred from the filename if omitted.
        plot: also save a PNG plot next to the data file.
    """
    from psychopy_mcp import analysis
    p = _resolve(path)
    return analysis.analyze(str(p), paradigm=paradigm or None, plot=plot)


@mcp.tool()
def export_web(key: str, name: str = "") -> dict:
    """Export a paradigm to a Builder .psyexp + PsychoJS .js for ONLINE studies.

    Only Builder experiments transpile to JavaScript and run online on Pavlovia;
    this builds one (instructions + fixation + stimulus + keyboard, looped over a
    generated conditions CSV) and compiles it to .js. Upload the output folder to
    Pavlovia (or sync from the PsychoPy Builder) to run web subjects.

    Currently supports single-text-stimulus choice paradigms (stroop, flanker,
    lexdecision, and text-based custom paradigms); shape/multi-phase paradigms
    return a clear message and stay desktop-only.

    Args:
        key: paradigm key (see list_paradigms).
        name: output name (defaults to web_<key>); files go to workspace/<name>/.
    """
    from psychopy_mcp import web
    safe = "".join(c for c in (name or f"web_{key}") if c.isalnum() or c in "-_").strip("-_") or f"web_{key}"
    out_dir = WORKSPACE / safe
    try:
        return web.export(key, safe, str(out_dir))
    except ValueError as e:
        return {"error": str(e)}


@mcp.tool()
def export_for_spss(path: str, aggregate: bool = False) -> dict:
    """Write an analysis-ready CSV for the SPSS-MCP server to import.

    Bridges this server with SPSS-MCP: PsychoPy collects data here, this emits a
    clean CSV, then (in a session that also has SPSS-MCP configured) SPSS imports
    it and runs the stats — design → run → analyse in one conversation.

    Args:
        path: paradigm data CSV (relative resolves under workspace).
        aggregate: if true, write per participant x condition means (long format
                   for repeated-measures ANOVA); else one tidy row per trial.
    """
    from psychopy_mcp import analysis
    p = _resolve(path)
    return analysis.to_spss(str(p), aggregate=aggregate)


# ───────────────────────── builder (.psyexp) ─────────────────────────


@mcp.tool()
def read_psyexp(path: str) -> dict:
    """Parse a Builder .psyexp file into a structured summary.

    Returns the experiment settings, flow order, and each routine's components
    with their key parameters — enough to understand or modify the experiment.

    Args:
        path: .psyexp file (relative resolves under workspace).
    """
    import xml.etree.ElementTree as ET

    p = _resolve(path)
    if not p.exists():
        return {"error": f"not found: {p}"}
    try:
        root = ET.parse(p).getroot()
    except Exception as e:
        return {"error": repr(e)}
    routines = {}
    for routine in root.findall("./Routines/Routine"):
        comps = []
        for comp in routine:
            params = {}
            for prm in comp.findall("Param"):
                params[prm.get("name")] = prm.get("val")
            comps.append({"type": comp.tag, "name": comp.get("name"), "params": params})
        routines[routine.get("name")] = comps
    flow = []
    for node in root.findall("./Flow/*"):
        flow.append({"tag": node.tag, "name": node.get("name")})
    return {
        "version": root.get("version"),
        "flow": flow,
        "routines": routines,
    }


@mcp.tool()
def compile_psyexp(path: str, out: str = "") -> dict:
    """Compile a Builder .psyexp file into a runnable PsychoPy Python script.

    Args:
        path: .psyexp file (relative resolves under workspace).
        out: output .py path; defaults to the same name with .py extension.
    """
    p = _resolve(path)
    if not p.exists():
        return {"error": f"not found: {p}"}
    target = _resolve(out) if out else p.with_suffix(".py")
    code = (
        "import sys\n"
        "from psychopy.scripts.psyexpCompile import compileScript\n"
        "compileScript(infile=sys.argv[1], outfile=sys.argv[2])\n"
    )
    r = subprocess.run(
        [_py(), "-c", code, str(p), str(target)],
        capture_output=True, text=True, timeout=120,
    )
    if r.returncode != 0:
        return {"ok": False, "stderr": r.stderr[-4000:], "stdout": r.stdout[-2000:]}
    return {"ok": True, "out": str(target)}


# ───────────────────────── live control ─────────────────────────

_live_lock = threading.Lock()
_live_proc: Optional[subprocess.Popen] = None


@mcp.tool()
def live_start(
    fullscreen: bool = False,
    size: Optional[list[int]] = None,
    color: str = "gray",
    units: str = "height",
) -> dict:
    """Start a persistent PsychoPy window you can drive interactively.

    Opens a separate process that holds a Window and accepts commands via
    live_cmd (present text/images/shapes, flip, collect key/mouse responses,
    run arbitrary PsychoPy code, screenshot). Use this to pilot/inspect stimuli
    interactively. Call live_stop when done.

    Args:
        fullscreen: open fullscreen.
        size: [w, h] window size when not fullscreen (default [1024, 768]).
        color: background color name or rgb.
        units: PsychoPy units ("height", "norm", "pix", "deg").
    """
    global _live_proc
    with _live_lock:
        if _live_proc and _live_proc.poll() is None:
            return {"error": "live session already running; call live_stop first"}
        cfg = {
            "fullscreen": fullscreen,
            "size": size or [1024, 768],
            "color": color,
            "units": units,
        }
        _live_proc = subprocess.Popen(
            [_py(), "-u", str(LIVE_SCRIPT)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1, cwd=str(WORKSPACE),
        )
        resp = _live_send({"cmd": "init", "params": cfg}, timeout=60)
        return resp


def _live_send(obj: dict, timeout: float = 30) -> dict:
    """Send one JSON command and read exactly one JSON response line."""
    global _live_proc
    if not _live_proc or _live_proc.poll() is not None:
        return {"error": "no live session; call live_start"}
    try:
        _live_proc.stdin.write(json.dumps(obj) + "\n")
        _live_proc.stdin.flush()
    except Exception as e:
        return {"error": f"write failed: {e!r}"}

    result: dict = {}
    done = threading.Event()

    def _read():
        nonlocal result
        try:
            line = _live_proc.stdout.readline()
            result = json.loads(line) if line.strip() else {"error": "empty response"}
        except Exception as e:
            result = {"error": f"read failed: {e!r}"}
        finally:
            done.set()

    threading.Thread(target=_read, daemon=True).start()
    if not done.wait(timeout):
        return {"error": f"live command timed out after {timeout}s"}
    return result


@mcp.tool()
def live_cmd(command: str, params: Optional[dict] = None) -> dict:
    """Send a command to the live PsychoPy window (see live_start).

    Commands:
      present_text   params: text, color, pos[ x,y], height, wait_keys(list|null), max_wait
      present_image  params: image(path), size, pos, wait_keys, max_wait
      present_shape  params: shape("rect"|"circle"|"line"|"polygon"), size, pos, color, fillColor
      flip           present the back buffer
      clear          flip a blank screen
      wait_keys      params: keys(list|null), max_wait(sec) -> {key, rt}
      screenshot     params: filename -> saves PNG, returns path
      exec           params: code  -> runs Python with win, visual, core, event in scope
      info           window/frame-rate info
    Args:
        command: one of the above.
        params: command parameters (see above).
    """
    return _live_send({"cmd": command, "params": params or {}}, timeout=300)


@mcp.tool()
def live_status() -> dict:
    """Report whether a live PsychoPy session is currently running."""
    running = bool(_live_proc and _live_proc.poll() is None)
    return {"running": running}


@mcp.tool()
def live_stop() -> dict:
    """Close the live PsychoPy window and stop its process."""
    global _live_proc
    with _live_lock:
        if not _live_proc or _live_proc.poll() is not None:
            return {"running": False, "message": "no live session"}
        _live_send({"cmd": "quit", "params": {}}, timeout=10)
        try:
            _live_proc.wait(timeout=5)
        except Exception:
            _live_proc.kill()
        code = _live_proc.returncode
        _live_proc = None
        return {"running": False, "exit_code": code}


if __name__ == "__main__":
    mcp.run()
