"""Canonical effect analysis for paradigm data.

Reads a data CSV produced by the engine and computes the paradigm's standard
dependent variable (Stroop effect, flanker/Simon congruency effect, Posner
validity effect, search/Sternberg slope, switch cost, N-back d-prime, ANT
network scores, Go/No-Go commission rate), plus mean RT and accuracy per
condition, and optionally saves a plot.

Everything degrades gracefully: if a paradigm-specific column is missing it
falls back to a generic per-condition RT/accuracy summary.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

# which analysis each paradigm key uses
ANALYSIS = {
    "stroop": "conflict", "flanker": "conflict", "simon": "conflict",
    "dotprobe": "conflict",
    "posner": "posner",
    "gonogo": "gonogo",
    "sternberg": "slope_setsize", "visualsearch": "slope_setsize",
    "mentalrotation": "slope_angle",
    "taskswitch": "switchcost",
    "nback": "nback",
    "ant": "ant",
    "deception": "deception",
}
# condition naming per conflict paradigm: (baseline, interference)
_CONFLICT_PAIR = {"congruent": "incongruent"}


def _native(obj):
    """Recursively convert numpy scalars/containers to plain Python (JSON-safe)."""
    import numpy as np
    if isinstance(obj, dict):
        return {k: _native(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_native(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    return obj


def _num(series):
    import pandas as pd
    return pd.to_numeric(series, errors="coerce")


def _rt_by_condition(df, correct_only=True):
    import pandas as pd
    d = df.copy()
    d["rt"] = _num(d["rt"])
    if correct_only and "correct" in d.columns:
        d = d[_num(d["correct"]) == 1]
    g = d.dropna(subset=["rt"]).groupby("condition")["rt"]
    return {k: round(float(v), 4) for k, v in g.mean().items()}


def _acc_by_condition(df):
    if "correct" not in df.columns:
        return {}
    d = df.copy()
    d["correct"] = _num(d["correct"])
    g = d.dropna(subset=["correct"]).groupby("condition")["correct"]
    return {k: round(float(v), 4) for k, v in g.mean().items()}


def _linfit(xs, ys):
    """Return (slope, intercept) via least squares; needs >=2 distinct x."""
    import numpy as np
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    if len(set(xs)) < 2:
        return None, None
    slope, intercept = np.polyfit(xs, ys, 1)
    return round(float(slope), 5), round(float(intercept), 4)


def analyze(csv_path: str, paradigm: Optional[str] = None,
            plot: bool = True, plot_dir: Optional[str] = None) -> dict:
    import pandas as pd

    p = Path(csv_path)
    if not p.exists():
        return {"error": f"not found: {p}"}
    df = pd.read_csv(p)
    if "condition" not in df.columns:
        return {"error": "no 'condition' column; not a paradigm data file"}

    key = (paradigm or _infer(p)).lower() if (paradigm or _infer(p)) else None
    kind = ANALYSIS.get(key, "generic")

    rt = _rt_by_condition(df)
    acc = _acc_by_condition(df)
    out: dict = {"paradigm": key, "analysis": kind, "n_trials": int(len(df)),
                 "mean_rt_by_condition": rt, "accuracy_by_condition": acc}

    if kind == "conflict":
        if "congruent" in rt and "incongruent" in rt:
            out["effect_ms"] = round((rt["incongruent"] - rt["congruent"]) * 1000, 1)
            out["effect_label"] = "congruency effect (incongruent - congruent), ms"
    elif kind == "posner":
        if "valid" in rt and "invalid" in rt:
            out["effect_ms"] = round((rt["invalid"] - rt["valid"]) * 1000, 1)
            out["effect_label"] = "validity effect (invalid - valid), ms"
    elif kind == "switchcost":
        if "switch" in rt and "repeat" in rt:
            out["effect_ms"] = round((rt["switch"] - rt["repeat"]) * 1000, 1)
            out["effect_label"] = "switch cost (switch - repeat), ms"
    elif kind == "deception":
        if "lie" in rt and "truth" in rt:
            out["effect_ms"] = round((rt["lie"] - rt["truth"]) * 1000, 1)
            out["effect_label"] = "lie effect (lie - truth), ms"
    elif kind == "gonogo":
        out.update(_gonogo(df))
    elif kind == "slope_setsize":
        out.update(_slope(df, "set_size", "ms/item"))
    elif kind == "slope_angle":
        out.update(_slope(df, "angle", "ms/deg"))
    elif kind == "nback":
        out.update(_nback(df))
    elif kind == "ant":
        out.update(_ant(df, rt))

    if plot:
        try:
            out["plot"] = _plot(df, out, p, kind, plot_dir)
        except Exception as e:
            out["plot_error"] = repr(e)
    return _native(out)


def to_spss(csv_path: str, aggregate: bool = False,
            out: Optional[str] = None) -> dict:
    """Write an analysis-ready CSV for SPSS (import via the SPSS-MCP server).

    tidy (default): one row per valid trial with participant, condition, rt_ms,
    correct — ready for SPSS to aggregate/model.
    aggregate=True: per participant x condition means (mean_rt_ms on correct
    trials + accuracy), the long format for a repeated-measures ANOVA.
    """
    import pandas as pd
    p = Path(csv_path)
    if not p.exists():
        return {"error": f"not found: {p}"}
    df = pd.read_csv(p)
    if "condition" not in df.columns:
        return {"error": "no 'condition' column; not a paradigm data file"}

    part = "participant" if "participant" in df.columns else None
    df = df.copy()
    if part is None:
        df["participant"] = p.stem.split("_")[0]
    df["rt_ms"] = _num(df["rt"]) * 1000
    if "correct" in df.columns:
        df["correct"] = _num(df["correct"])
    else:
        df["correct"] = pd.NA

    keep = ["participant", "condition", "rt_ms", "correct"]
    tidy = df[[c for c in keep if c in df.columns]].dropna(subset=["condition"])

    if aggregate:
        corr = tidy[tidy["correct"] == 1] if "correct" in tidy else tidy
        rt = corr.dropna(subset=["rt_ms"]).groupby(["participant", "condition"])["rt_ms"].mean()
        acc = tidy.groupby(["participant", "condition"])["correct"].mean()
        result = rt.round(1).reset_index().rename(columns={"rt_ms": "mean_rt_ms"})
        result["accuracy"] = acc.round(4).reset_index()["correct"]
        suffix = "_spss_agg.csv"
    else:
        result = tidy.round({"rt_ms": 1})
        suffix = "_spss.csv"

    dest = Path(out) if out else p.with_name(p.stem + suffix)
    result.to_csv(dest, index=False)
    return {"path": str(dest), "rows": int(len(result)),
            "columns": list(result.columns), "aggregate": aggregate,
            "next": f"In a session with SPSS-MCP configured: import '{dest.name}' "
                    f"then run a t-test/ANOVA on rt_ms by condition."}


def _infer(p: Path) -> Optional[str]:
    name = p.stem.lower()
    for key in ANALYSIS:
        if key in name:
            return key
    return None


def _gonogo(df):
    import pandas as pd
    d = df.copy()
    d["correct"] = _num(d["correct"])
    res = {}
    nogo = d[d["condition"] == "nogo"]
    go = d[d["condition"] == "go"]
    if len(nogo):
        res["commission_error_rate"] = round(1 - nogo["correct"].mean(), 4)
    if len(go):
        res["omission_rate"] = round(1 - go["correct"].mean(), 4)
        gort = _num(go[go["correct"] == 1]["rt"]).dropna()
        if len(gort):
            res["go_rt_ms"] = round(gort.mean() * 1000, 1)
    res["effect_label"] = "commission error rate on No-Go (response inhibition)"
    return res


def _slope(df, col, unit):
    import pandas as pd
    if col not in df.columns:
        return {"note": f"no '{col}' column; skipped slope"}
    d = df.copy()
    d["rt"] = _num(d["rt"])
    if "correct" in d.columns:
        d = d[_num(d["correct"]) == 1]
    d[col] = _num(d[col])
    g = d.dropna(subset=["rt", col]).groupby(col)["rt"].mean()
    slope, intercept = _linfit(g.index.tolist(), g.values.tolist())
    return {
        "rt_by_level_ms": {int(k): round(v * 1000, 1) for k, v in g.items()},
        "slope": None if slope is None else round(slope * 1000, 2),
        "slope_unit": unit,
        "intercept_ms": None if intercept is None else round(intercept * 1000, 1),
        "effect_label": f"search/scan slope ({unit})",
    }


def _nback(df):
    import pandas as pd
    if "is_target" not in df.columns:
        return {"note": "no 'is_target' column; skipped d-prime"}
    import numpy as np
    from math import erf, sqrt
    d = df.copy()
    d["is_target"] = _num(d["is_target"])
    responded = d["response"].notna() & (d["response"].astype(str) != "nan") & \
        (d["response"].astype(str) != "")
    tgt = d["is_target"] == 1
    hits = (responded & tgt).sum()
    misses = (~responded & tgt).sum()
    fas = (responded & ~tgt).sum()
    crs = (~responded & ~tgt).sum()

    def _z(p):
        p = min(max(p, 1e-3), 1 - 1e-3)
        # inverse normal CDF via rational approximation
        import statistics
        return statistics.NormalDist().inv_cdf(p)

    hr = hits / max(hits + misses, 1)
    far = fas / max(fas + crs, 1)
    dprime = round(_z(hr) - _z(far), 3)
    return {"hits": int(hits), "misses": int(misses), "false_alarms": int(fas),
            "correct_rejections": int(crs), "hit_rate": round(hr, 3),
            "false_alarm_rate": round(far, 3), "d_prime": dprime,
            "effect_label": "d-prime (sensitivity)"}


def _ant(df, rt):
    res = {"networks_ms": {}}
    # alerting/orienting need cue conditions; conflict needs flanker meta
    if {"nocue", "doublecue"} <= set(rt):
        res["networks_ms"]["alerting"] = round((rt["nocue"] - rt["doublecue"]) * 1000, 1)
    if {"centercue", "spatialcue"} <= set(rt):
        res["networks_ms"]["orienting"] = round((rt["centercue"] - rt["spatialcue"]) * 1000, 1)
    if "flanker" in df.columns:
        import pandas as pd
        d = df.copy()
        d["rt"] = _num(d["rt"])
        if "correct" in d.columns:
            d = d[_num(d["correct"]) == 1]
        g = d.dropna(subset=["rt"]).groupby("flanker")["rt"].mean()
        if {"congruent", "incongruent"} <= set(g.index):
            res["networks_ms"]["executive"] = round((g["incongruent"] - g["congruent"]) * 1000, 1)
    res["effect_label"] = "ANT network scores (alerting/orienting/executive), ms"
    return res


def _plot(df, out, src: Path, kind: str, plot_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plot_dir = Path(plot_dir) if plot_dir else src.parent
    plot_dir.mkdir(parents=True, exist_ok=True)
    dest = plot_dir / (src.stem + "_analysis.png")

    fig, ax = plt.subplots(figsize=(6, 4))
    if kind in ("slope_setsize", "slope_angle") and "rt_by_level_ms" in out:
        lv = out["rt_by_level_ms"]
        xs, ys = list(lv.keys()), list(lv.values())
        ax.plot(xs, ys, "o-")
        ax.set_xlabel("set size / angle"); ax.set_ylabel("RT (ms)")
        if out.get("slope") is not None:
            ax.set_title(f"{out.get('paradigm','')}  slope={out['slope']} {out.get('slope_unit','')}")
    else:
        rt = out.get("mean_rt_by_condition", {})
        if rt:
            ax.bar([str(k) for k in rt], [v * 1000 for v in rt.values()])
            ax.set_ylabel("RT (ms)")
        title = out.get("paradigm", "")
        if "effect_ms" in out:
            title += f"   effect = {out['effect_ms']} ms"
        ax.set_title(title)
    fig.tight_layout()
    fig.savefig(dest, dpi=110)
    plt.close(fig)
    return str(dest)
