"""Brick warehouse / loft: pilastered brick facade, arched multi-pane windows, loading-dock doors with an
iron canopy, corbelled cornice, fire escape, rooftop water tank and boiler stack. Runs inside Blender."""

import math
import random
from typing import Dict

from rbxasset.builders import arch
from rbxasset.builders.arch import Face, Op, win
from rbxasset.builders.kit import Kit
from rbxasset.builders.result import BuildResult

TAGS = (
    "base",
    "wall",
    "wall_b",
    "trim",
    "sash",
    "glass",
    "door",
    "soot",
    "iron",
    "groove",
    "wood",
    "roof",
    "ground",
    "curb",
    "road",
)
T0, BH = 0.55, 1.4


def build(params: Dict, rng: random.Random) -> BuildResult:
    W, D, F, FH, bays = (
        params[x] for x in ("width", "depth", "floors", "floor_height", "bays")
    )
    k = Kit(TAGS)
    T = {r: r for r in TAGS}
    TB = dict(T, wall="base", wall_b="base")
    zE = BH + F * FH
    bay = W / bays
    cs = [-W / 2 + (i + 0.5) * bay for i in range(bays)]
    f = Face(k, "front", W, D)
    k.box("base", (W + 0.3, D + 0.3, BH), (0, 0, BH / 2), bevel=0.0)
    # front: ground-floor docks and barred arches, arched loft windows above
    ops = []
    for i, u in enumerate(cs):
        if i % 2 == 0:
            ops.append(Op("bigdoor", u - 3.4, u + 3.4, BH, BH + 9.0))
        else:
            ops.append(Op("arch", u - 2.4, u + 2.4, BH + 2.0, BH + 9.6))
    for fl in range(1, F):
        z = BH + fl * FH
        for u in cs:
            ops.append(Op("arch", u - 2.4, u + 2.4, z + 1.6, z + FH - 1.6))
    arch.wall(f, T, BH, zE, ops, T0, rng, panel=4.0, vstep=FH, variant=0.35)
    for side, n in (("back", bays), ("left", 5), ("right", 5)):
        Fa = Face(k, side, W, D)
        L = Fa.L
        sops = [
            Op(
                "window",
                -L / 2 + (i + 0.5) * L / n - 2.1,
                -L / 2 + (i + 0.5) * L / n + 2.1,
                BH + fl * FH + 1.8,
                BH + (fl + 1) * FH - 1.8,
                style="plain",
                rows=3,
                cols=3,
                soot=False,
            )
            for fl in range(F)
            for i in range(n)
        ]
        arch.wall(Fa, T, BH, zE, sops, T0, rng, panel=4.0, vstep=FH, variant=0.35)
    # pilasters and string courses
    for i in range(bays + 1):
        u = -W / 2 + i * bay
        f.box("wall_b", u, BH + (zE - BH) / 2, 1.4, zE - BH, 0.5, 0.6)
    for fl in range(1, F):
        arch.course(
            k,
            "trim",
            W,
            D,
            BH + fl * FH,
            proj=0.3,
            h=0.55,
            sides=("front", "left", "right"),
        )
        f.box("soot", 0, BH + fl * FH - 0.9, W, 1.0, 0.03, 0.05)
    # corbelled cornice and parapet
    for i, (pr, hh) in enumerate(((0.3, 0.5), (0.6, 0.5), (0.9, 0.55))):
        arch.course(
            k,
            "wall_b",
            W,
            D,
            zE - 1.4 + i * 0.52,
            proj=pr,
            h=hh,
            sides=("front", "left", "right"),
        )
    arch.cornice(
        k,
        T,
        W,
        D,
        zE + 1.8,
        proj=1.4,
        h=1.8,
        brackets=False,
        dentils=True,
        sides=("front", "left", "right"),
    )
    for sy in (-1, 1):
        k.box("wall", (W, T0, 2.0), (0, sy * (D / 2 - T0 / 2), zE + 1.0), bevel=0.0)
    for sx in (-1, 1):
        k.box(
            "wall",
            (T0, D - 2 * T0, 2.0),
            (sx * (W / 2 - T0 / 2), 0, zE + 1.0),
            bevel=0.0,
        )
    k.box("roof", (W - 0.2, D - 0.2, 0.4), (0, 0, zE + 0.2), bevel=0.0)
    # loading canopy over two docks, with hanger rods
    for u in (cs[0], cs[2]) if bays > 2 else (cs[0],):
        k.box("iron", (7.6, 3.6, 0.35), (u, -(D / 2 + 1.8), BH + 10.2), bevel=0.0)
        for sx in (-1, 1):
            k.box(
                "iron",
                (0.1, 0.1, 2.6),
                (u + sx * 3.5, -(D / 2 + 3.4), BH + 11.5),
                bevel=0.0,
            )
        k.box("iron", (7.8, 0.35, 0.6), (u, -(D / 2 + 3.6), BH + 10.0), bevel=0.0)
    if params["fire_escape"]:
        arch.fire_escape(
            Face(k, "right", W, D), T, 0.0, BH + FH, F - 1, FH, w=5.0, depth=1.8
        )
    arch.chimney(k, "wall_b", -W / 2 + 6.0, D / 4, zE, zE + 26.0, 3.2, 3.2, pots=0)
    k.box("trim", (4.0, 4.0, 0.7), (-W / 2 + 6.0, D / 4, zE + 25.8), bevel=0.0)
    if params["water_tank"]:
        tx, ty = W / 4, -D / 6
        for sx in (-1, 1):
            for sy in (-1, 1):
                k.box(
                    "iron",
                    (0.35, 0.35, 5.0),
                    (tx + sx * 3.0, ty + sy * 3.0, zE + 2.7),
                    bevel=0.0,
                )
        k.cyl("wood", 4.0, 7.0, (tx, ty, zE + 5.2 + 3.5), verts=20)
        for i in range(3):
            k.cyl("iron", 4.12, 0.2, (tx, ty, zE + 5.2 + 1.5 + i * 2.2), verts=20)
        k.cone("roof", 4.4, 0.2, 2.6, (tx, ty, zE + 5.2 + 7.0 + 1.3), verts=20)
    if params["street"]:
        arch.street_context(k, T, W + 8, D, front_depth=9.0, side=4.0)
    top = zE + 28.0
    shots = [
        ("wide", (-W * 1.0, -(D / 2 + W * 2.0), zE * 0.5), (0.0, 0.0, zE * 0.4), 34.0),
        ("front", (cs[0] + 2, -(D / 2 + 22), BH + 7), (cs[1], -D / 2, BH + 7), 42.0),
        ("roof", (W * 0.1, -(D / 2 + 28), zE + 6), (W / 5, -D / 6, zE + 6), 40.0),
    ]
    return BuildResult(k.parts, shots, {"W": W, "H": top})
