"""Shared helpers for building literature-grounded paradigm trial lists.

These keep every paradigm's trial-construction terse and consistent. Stimulus
positions/sizes flow from the paradigm spec, so conditions stay comparable.
"""
from __future__ import annotations

import math


# ── stimulus descriptors (plain dicts the engine knows how to draw) ──

def text(s, color="white", pos=(0.0, 0.0), height=0.1, bold=False,
         font="Arial", ori=0.0, flipHoriz=False):
    return {"kind": "text", "text": s, "color": color, "pos": list(pos),
            "height": height, "bold": bold, "font": font, "ori": ori,
            "flipHoriz": flipHoriz}


def rect(pos=(0.0, 0.0), size=(0.2, 0.2), lineColor="white", fillColor=None, ori=0.0):
    return {"kind": "rect", "pos": list(pos), "size": list(size),
            "lineColor": lineColor, "fillColor": fillColor, "ori": ori}


def circle(pos=(0.0, 0.0), radius=0.1, lineColor="white", fillColor=None):
    return {"kind": "circle", "pos": list(pos), "radius": radius,
            "lineColor": lineColor, "fillColor": fillColor}


def fixation(spec):
    """A standard central fixation stim from the spec's surface settings."""
    S = spec["surface"]
    return text(S.get("fixation_char", "+"), color="white",
                pos=S.get("stim_pos", [0.0, 0.0]),
                height=S.get("fixation_height", 0.05))


# ── phase builders ──

def phase(stims, dur=None, collect=False, keys=None):
    return {"stims": list(stims), "dur": dur, "collect": collect, "keys": keys}


def fixation_phase(spec):
    return phase([fixation(spec)], dur=spec["timing"].get("fixation_sec", 0.5))


def blank_phase(dur):
    return phase([], dur=dur)


def response_phase(stims, spec, keys):
    """A phase that shows `stims` until a key in `keys` or the response deadline."""
    return phase(stims, dur=spec["timing"].get("max_response_sec", 2.0),
                 collect=True, keys=keys)


# ── balancing helpers ──

def balanced_grid(layout_w=0.7, n=8, min_spacing=0.12, seed_offset=0, rng=None):
    """Return `n` jittered positions on an invisible grid filling a centred square.

    Used by visual search; positions deliberately VARY across trials (that is
    the paradigm), while item size stays fixed.
    """
    import random
    r = rng or random
    cells = max(int(math.ceil(math.sqrt(n / 0.45))), 3)  # leave the grid sparse
    coords = []
    step = layout_w / cells
    for i in range(cells):
        for j in range(cells):
            x = -layout_w / 2 + step * (i + 0.5)
            y = -layout_w / 2 + step * (j + 0.5)
            coords.append((x, y))
    r.shuffle(coords)
    out = []
    for (x, y) in coords[:n]:
        jit = step * 0.2
        out.append([x + r.uniform(-jit, jit), y + r.uniform(-jit, jit)])
    return out
