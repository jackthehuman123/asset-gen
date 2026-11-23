"""Rowhouse / brownstone: narrow tall facade, raised basement with stoop, cornice, flat roof."""

import math
import random
from typing import Dict

from rbxasset.builders import facade
from rbxasset.builders.kit import Kit
from rbxasset.builders.result import BuildResult

TAGS = ("foundation", "walls", "trim", "roof", "door", "glazing")
T, WIN_W, DOOR_W, DOOR_H = 0.35, 2.6, 3.2, 7.2


def build(params: Dict, rng: random.Random) -> BuildResult:
    W, D, F, FHt, BH = (
        params[x]
        for x in ("width", "depth", "floors", "floor_height", "basement_height")
    )
    bays = params["bays"]
    k = Kit(TAGS)
    tags = {"wall": "walls", "trim": "trim", "glazing": "glazing", "door": "door"}
    k.box("foundation", (W + 0.1, D + 0.1, BH), (0, 0, BH / 2), bevel=0.0)
    zE = BH + F * FHt
    front, back = [], []
    bay_u = facade.evenly(W, bays, WIN_W)
    door_uc = (bay_u[0][0] + bay_u[0][1]) / 2
    for f in range(F):
        z = BH + f * FHt
        for i, (u0, u1) in enumerate(bay_u):
            if f == 0 and i == 0:
                front.append(
                    ("door", door_uc - DOOR_W / 2, door_uc + DOOR_W / 2, z, z + DOOR_H)
                )
            else:
                h = 5.8 if f == 0 else 5.0
                front.append(("window", u0, u1, z + 1.6, z + 1.6 + h))
        for u0, u1 in facade.evenly(W, 2, WIN_W):
            back.append(("window", u0, u1, z + 2.4, z + 2.4 + 4.6))
    for side, ops in (("front", front), ("back", back), ("left", []), ("right", [])):
        facade.wall_with_openings(k, tags, side, W, D, T, BH, zE, ops)
    if params["cornice"]:
        k.box("trim", (W + 0.7, 1.0, 1.0), (0, -(D / 2 + 0.2), zE - 0.1), bevel=0.0)
        k.box("trim", (W + 0.3, 0.4, 0.8), (0, -(D / 2 + 0.05), zE - 1.2), bevel=0.0)
    for sy in (-1, 1):
        k.box("walls", (W, T, 1.3), (0, sy * (D / 2 - T / 2), zE + 0.65), bevel=0.0)
    for sx in (-1, 1):
        k.box(
            "walls",
            (T, D - 2 * T, 1.3),
            (sx * (W / 2 - T / 2), 0, zE + 0.65),
            bevel=0.0,
        )
    k.box("roof", (W - 0.2, D - 0.2, 0.3), (0, 0, zE + 0.15), bevel=0.0)
    if params["stoop"]:
        n = max(2, int(math.ceil(BH / 0.65)))
        rise = BH / n
        sw = DOOR_W + 1.2
        for i in range(n):
            k.box(
                "foundation",
                (sw, 1.0, rise * (n - i)),
                (door_uc, -(D / 2 + 0.5 + i * 1.0), rise * (n - i) / 2),
                bevel=0.0,
            )
        for sgn in (-1, 1):
            k.box(
                "trim",
                (0.35, 0.35, 3.2),
                (door_uc + sgn * (sw / 2 - 0.2), -(D / 2 + 0.2 + n * 1.0), 1.6),
                bevel=0.0,
            )
    top = zE + 1.3
    shots = [
        (
            "wide",
            (-top * 0.55, -(D / 2 + top * 1.25), top * 0.55),
            (0.0, -D * 0.1, top * 0.5),
            35.0,
        ),
        (
            "front",
            (door_uc - 4.0, -(D / 2 + 11), BH + 5),
            (door_uc, -D / 2, BH + 4),
            45.0,
        ),
    ]
    return BuildResult(k.parts, shots, {"W": W, "H": top})
