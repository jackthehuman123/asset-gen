"""Table: top, four legs, optional apron and stretchers. Runs inside Blender."""

import random
from typing import Dict

from rbxasset.builders.kit import Kit
from rbxasset.builders.kit_shots import default_shots
from rbxasset.builders.result import BuildResult

TAGS = ("top", "legs", "apron", "stretchers")


def build(params: Dict, rng: random.Random) -> BuildResult:
    W, D, H = params["width"], params["depth"], params["height"]
    T, L, A = params["top_thickness"], params["leg_size"], params["apron_height"]
    k = Kit(TAGS)
    k.box("top", (W, D, T), (0, 0, H - T / 2), bevel=0.02)
    inset = 0.12
    lx, ly, leg_h = W / 2 - inset - L / 2, D / 2 - inset - L / 2, H - T
    for sx in (-1, 1):
        for sy in (-1, 1):
            loc = (sx * lx, sy * ly, leg_h / 2)
            if params["leg_shape"] == "round":
                k.cyl("legs", L / 2, leg_h, loc, verts=14)
            else:
                k.box("legs", (L, L, leg_h), loc)
    if A > 0:
        z = H - T - A / 2
        for sy in (-1, 1):
            k.box("apron", (2 * lx - L, 0.06, A), (0, sy * ly, z))
        for sx in (-1, 1):
            k.box("apron", (0.06, 2 * ly - L, A), (sx * lx, 0, z))
    if params["stretchers"]:
        zs = min(0.5, leg_h * 0.25)
        for sx in (-1, 1):
            k.box("stretchers", (0.08, 2 * ly - L, 0.1), (sx * lx, 0, zs))
        k.box("stretchers", (2 * lx - L, 0.08, 0.1), (0, 0, zs))
    return BuildResult(k.parts, default_shots(W, D, H), {"W": W, "H": H})
