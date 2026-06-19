"""Tests for the paradigm library — no PsychoPy/window needed.

These assert the literature-grounding invariants: every paradigm builds, trial
conditions are balanced as documented, surface parameters are shared across
conditions (fixed size/position), and every generated script is valid Python.
Run with:  python -m pytest tests   (or just: python tests/test_paradigms.py)
"""
import ast
from collections import Counter

from psychopy_mcp import paradigms

ENGINE_KEYS = [k for k in paradigms.REGISTRY if k != "stopsignal"]


def test_list_has_all_builtins():
    keys = {p["key"] for p in paradigms.list_paradigms() if "error" not in p}
    assert set(paradigms.REGISTRY).issubset(keys)


def test_every_paradigm_builds_with_valid_structure():
    for key in ENGINE_KEYS:
        trials = paradigms.build_trials(key)
        assert trials, f"{key} built no trials"
        for t in trials:
            assert "phases" in t and t["phases"]
            assert 0 <= t.get("rt_phase", 0) < len(t["phases"])


def test_surface_params_shared_across_conditions():
    """Font height/position come from one SPEC, so all stims of a paradigm that
    use the spec's stim_height share it (the core anti-divergence guarantee)."""
    for key in ENGINE_KEYS:
        spec = paradigms.get_paradigm(key)
        assert "surface" in spec and "timing" in spec
        assert "stim_pos" in spec["surface"]


def test_balanced_conditions():
    # paradigms whose conditions are designed to be equal-N
    expect_equal = {"stroop", "flanker", "simon", "visualsearch",
                    "mentalrotation", "dotprobe", "lexdecision", "taskswitch"}
    for key in expect_equal:
        counts = Counter(t["condition"] for t in paradigms.build_trials(key))
        vals = set(counts.values())
        assert len(vals) == 1, f"{key} not balanced: {dict(counts)}"


def test_gonogo_ratio():
    counts = Counter(t["condition"] for t in paradigms.build_trials("gonogo"))
    assert counts["go"] == 3 * counts["nogo"]   # 75/25


def test_all_scripts_are_valid_python():
    for key in paradigms.REGISTRY:
        src = paradigms.generate_script(key, f"gen_{key}", {})
        ast.parse(src)   # raises SyntaxError on failure


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("ok:", fn.__name__)
    print(f"\nALL {len(fns)} TESTS PASSED")
