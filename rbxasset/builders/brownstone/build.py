"""NYC brownstone: raised basement with stoop, brownstone front with hooded windows, string courses,
bracketed cornice, brick party walls, flat roof with parapet, sidewalk context. Runs inside Blender."""
import math
import random
from typing import Dict

from rbxasset.builders import arch
from rbxasset.builders.arch import Face, win
from rbxasset.builders.kit import Kit
from rbxasset.builders.result import BuildResult

TAGS = ("base", "wall", "wall_b", "brick", "trim", "sash", "glass", "door", "soot", "iron", "groove",
        "roof", "ground", "curb", "road")
T0 = 0.45


def build(params: Dict, rng: random.Random) -> BuildResult:
    W, D, F, FH, BH = (params[x] for x in ("width", "depth", "floors", "floor_height", "basement_height"))
    bays = params["bays"]
    k = Kit(TAGS)
    T = {r: r for r in TAGS}
    TB = dict(T, wall="base", wall_b="base")
    TS = dict(T, wall="brick", wall_b="brick", soot="brick")
    zE = BH + F * FH
    front = Face(k, "front", W, D)
    centers = [-W / 2 + (i + 0.5) * W / bays for i in range(bays)]
    door_u = centers[0]

    # basement: rusticated stone, barred windows, areaway door under the stoop
    ops = [win(u, 0.9, 2.6, 2.4, rows=2, cols=2, style="plain", soot=False) for u in centers[1:]]
    ops.append(arch.Op("door", door_u - 1.5, door_u + 1.5, 0.0, 3.6, hood=False))
    arch.wall(front, TB, 0.0, BH, ops, T0, rng)
    for side in ("back", "left", "right"):
        arch.wall(Face(k, side, W, D), TB, 0.0, BH, [], T0, rng)
    arch.rustication(k, "groove", W, D, 0.5, BH, h=1.0)
    for u in centers[1:]:
        for j in range(5):
            k.box("iron", (0.06, 0.06, 2.4), (u - 1.0 + j * 0.5, -(D / 2 + 0.12), 2.1), bevel=0.0)

    # front: floors of hooded / surround / plain windows
    fops = []
    for f in range(F):
        z = BH + f * FH
        h, sill, style = (7.4, 1.5, "hooded") if f == 0 else (7.0, 1.6, "hooded") if f == 1 else \
                         (6.2, 1.8, "surround") if f < F - 1 else (5.0, 2.0, "plain")
        for i, u in enumerate(centers):
            if f == 0 and i == 0:
                fops.append(arch.Op("door", u - 1.9, u + 1.9, z, z + 8.0, transom=1.8, hood=True))
            else:
                fops.append(win(u, z + sill, 2.8, h, style=style, rows=3 if h > 6 else 2, cols=2))
    arch.wall(front, T, BH, zE, fops, T0, rng, panel=5.0, vstep=FH)
    # sides and back: brick, windows on the back only
    bops = [win(u, BH + f * FH + 2.0, 2.6, 5.4, style="plain", soot=False)
            for f in range(F) for u in (-W / 4, W / 4)]
    arch.wall(Face(k, "back", W, D), TS, BH, zE, bops, T0, rng, panel=5.0)
    for side in ("left", "right"):
        arch.wall(Face(k, side, W, D), TS, BH, zE, [], T0, rng, panel=7.0, vstep=FH)

    # string courses, quoin-like corner piers and the cornice
    for f in range(0, F + 1):
        arch.course(k, "trim", W, D, BH + f * FH, proj=0.3, h=0.5, sides=("front",))
    
    if params["cornice"]:
        arch.cornice(k, T, W, D, zE + 0.8, proj=1.7, h=2.6, brackets=True, dentils=True, step=1.2, sides=("front",))
    front.box("soot", 0, zE - 1.6, W - 0.4, 0.9, 0.03, 0.05)
    # parapet + roof + bulkhead
    k.box("wall", (W, T0, 1.4), (0, -(D / 2 - T0 / 2), zE + 0.7), bevel=0.0)
    k.box("brick", (W, T0, 1.4), (0, D / 2 - T0 / 2, zE + 0.7), bevel=0.0)
    for sx in (-1, 1):
        k.box("brick", (T0, D - 2 * T0, 1.4), (sx * (W / 2 - T0 / 2), 0, zE + 0.7), bevel=0.0)
    k.box("trim", (W + 0.3, 0.7, 0.3), (0, -(D / 2 - 0.1), zE + 1.55), bevel=0.0)
    k.box("roof", (W - 0.2, D - 0.2, 0.35), (0, 0, zE + 0.17), bevel=0.0)
    k.box("brick", (W * 0.35, 5.0, 3.5), (W * 0.2, D * 0.12, zE + 2.1), bevel=0.0)
    arch.chimney(k, "brick", -W * 0.3, D * 0.25, zE, zE + 3.5, 1.5, 1.5)

    # stoop with iron rails
    if params["stoop"]:
        n = max(2, int(math.ceil(BH / 0.62)))
        rise, run, sw = BH / n, 1.1, 5.2
        for i in range(n):
            k.box("base", (sw, run, rise * (n - i)), (door_u, -(D / 2 + 0.55 + i * run), rise * (n - i) / 2), bevel=0.0)
            k.box("trim", (sw + 0.2, run + 0.05, 0.14), (door_u, -(D / 2 + 0.55 + i * run), rise * (n - i) + 0.07), bevel=0.0)
        k.box("base", (sw + 0.6, 2.2, BH), (door_u, -(D / 2 + 1.1 - 2.2 / 2 + 0.55), BH / 2), bevel=0.0)
        ang = math.atan2(rise, run)
        length = math.hypot(n * run, BH)
        for sgn in (-1, 1):
            x = door_u + sgn * (sw / 2 - 0.15)
            ymid = -(D / 2 + 0.2 + n * run / 2)
            k.box("iron", (0.12, length, 0.12), (x, ymid, BH + 3.0 - BH / 2 + 0.0), rot=(ang, 0, 0), bevel=0.0)
            for i in range(n + 1):
                yy = -(D / 2 + 0.2 + i * run)
                zz = BH - i * rise
                k.box("iron", (0.07, 0.07, 3.0), (x, yy, zz + 1.5), bevel=0.0)
            for yy, zz in ((-(D / 2 + 0.2), BH), (-(D / 2 + 0.2 + n * run), 0.0)):
                k.box("iron", (0.3, 0.3, 3.6), (x, yy, zz + 1.8), bevel=0.0)
    if params["street"]:
        arch.street_context(k, T, W, D, front_depth=7.0, side=5.0)
    top = zE + 1.7
    shots = [
        ("wide", (-top * 0.7, -(D / 2 + top * 1.9), top * 0.45), (0.0, -D * 0.1, top * 0.45), 34.0),
        ("front", (door_u - 5, -(D / 2 + 14), BH + 7), (door_u, -D / 2, BH + 5), 42.0),
        ("cornice", (-3.0, -(D / 2 + 13), zE - 1), (0.0, -D / 2, zE), 48.0),
    ]
    return BuildResult(k.parts, shots, {"W": W, "H": top})
