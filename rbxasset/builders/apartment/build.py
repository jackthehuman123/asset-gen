"""Apartment block: window-grid facades, ground-floor entrance with canopy, flat roof with parapet."""
import random
from typing import Dict

from rbxasset.builders import facade
from rbxasset.builders.kit import Kit
from rbxasset.builders.result import BuildResult

TAGS = ("foundation", "walls", "trim", "roof", "door", "glazing")
T, WIN_W, WIN_H, SILL, DOOR_W, DOOR_H, PL = 0.4, 2.4, 3.6, 2.4, 3.6, 6.4, 1.0


def build(params: Dict, rng: random.Random) -> BuildResult:
    W, D, F, FHt = (params[x] for x in ("width", "depth", "floors", "floor_height"))
    cols, scols = params["columns"], params["side_columns"]
    k = Kit(TAGS)
    tags = {"wall": "walls", "trim": "trim", "glazing": "glazing", "door": "door"}
    k.box("foundation", (W + 0.2, D + 0.2, PL), (0, 0, PL / 2), bevel=0.0)
    zE = PL + F * FHt

    def grid(L, n, door_at=None):
        ops = []
        for f in range(F):
            z = PL + f * FHt
            for i, (u0, u1) in enumerate(facade.evenly(L, n, WIN_W) if n else []):
                if f == 0 and i == door_at:
                    uc = (u0 + u1) / 2
                    ops.append(("door", uc - DOOR_W / 2, uc + DOOR_W / 2, z, z + DOOR_H))
                else:
                    ops.append(("window", u0, u1, z + SILL, z + SILL + WIN_H))
        return ops

    door_i = cols // 2
    ops = {"front": grid(W, cols, door_i), "back": grid(W, cols), "left": grid(D, scols), "right": grid(D, scols)}
    for side in facade.SIDES:
        facade.wall_with_openings(k, tags, side, W, D, T, PL, zE, ops[side])
    for f in range(1, F + 1):
        k.box("trim", (W + 0.3, D + 0.3, 0.22), (0, 0, PL + f * FHt - 0.11), bevel=0.0)
    door_uc = sum(facade.evenly(W, cols, WIN_W)[door_i]) / 2
    k.box("trim", (DOOR_W + 2.4, 2.4, 0.3), (door_uc, -(D / 2 + 1.2), PL + DOOR_H + 0.9), bevel=0.0)
    for sy in (-1, 1):
        k.box("walls", (W, T, 1.2), (0, sy * (D / 2 - T / 2), zE + 0.6), bevel=0.0)
    for sx in (-1, 1):
        k.box("walls", (T, D - 2 * T, 1.2), (sx * (W / 2 - T / 2), 0, zE + 0.6), bevel=0.0)
    k.box("roof", (W - 0.2, D - 0.2, 0.3), (0, 0, zE + 0.15), bevel=0.0)
    k.box("walls", (W * 0.22, D * 0.3, 4.0), (W * 0.2, 0, zE + 2.0), bevel=0.0)
    top = zE + 4.0
    s = max(W, D, top)
    shots = [
        ("wide", (-s * 0.9, -(D / 2 + s * 1.5), top * 0.55), (0.0, 0.0, top * 0.5), 38.0),
        ("front", (door_uc - 6, -(D / 2 + 14), PL + 6), (door_uc, -D / 2, PL + 5), 45.0),
    ]
    return BuildResult(k.parts, shots, {"W": W, "H": top})
