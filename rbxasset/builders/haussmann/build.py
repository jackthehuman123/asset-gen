"""Haussmann apartment building: rusticated ground floor with arches, entresol, 'noble' floor with
pedimented windows and a continuous iron balcony, plain floors, bracketed cornice, zinc mansard with
dormers and chimney stacks. Runs inside Blender."""
import math
import random
from typing import Dict

from rbxasset.builders import arch
from rbxasset.builders.arch import Face, Op, win
from rbxasset.builders.kit import Kit
from rbxasset.builders.result import BuildResult

TAGS = ("base", "wall", "wall_b", "trim", "sash", "glass", "door", "soot", "iron", "groove", "roof",
        "ground", "curb", "road")
T0, GFH, ENT = 0.5, 12.5, 8.0


def build(params: Dict, rng: random.Random) -> BuildResult:
    W, D, F, FH, bays = (params[x] for x in ("width", "depth", "floors", "floor_height", "bays"))
    k = Kit(TAGS)
    T = {r: r for r in TAGS}
    TB = dict(T, wall="base", wall_b="base")
    bay = W / bays
    cs = [-W / 2 + (i + 0.5) * bay for i in range(bays)]
    mid = bays // 2
    f = Face(k, "front", W, D)
    # levels: ground, entresol, noble, then plain floors
    levels = [("ground", GFH), ("entresol", ENT), ("noble", FH * 1.25)] + [("plain", FH)] * max(0, F - 2)
    zs = [0.0]
    for _, h in levels:
        zs.append(zs[-1] + h)
    zE = zs[-1]
    # ground floor: rusticated, arched openings, central carriage door
    ops = []
    for i, u in enumerate(cs):
        if i == mid:
            ops.append(Op("arch", u - 3.3, u + 3.3, 0.0, 11.0, door=True))
        else:
            ops.append(Op("arch", u - 1.8, u + 1.8, 1.6, 10.2))
    arch.wall(f, TB, 0.0, GFH, ops, T0, rng, panel=5.0, vstep=GFH)
    arch.rustication(k, "groove", W, D, 0.0, GFH, h=1.3)
    for side in ("back", "left", "right"):
        arch.wall(Face(k, side, W, D), TB, 0.0, GFH, [], T0, rng, panel=6.0, vstep=GFH)
    # upper floors
    fops = []
    for li, (name, h) in enumerate(levels[1:], start=1):
        z = zs[li]
        for i, u in enumerate(cs):
            if name == "entresol":
                fops.append(win(u, z + 2.0, 2.6, 3.8, style="plain", rows=2, cols=2))
            elif name == "noble":
                fops.append(win(u, z + 0.8, 3.2, h - 2.0, style="pediment" if i % 2 == 0 else "hooded", rows=4, cols=2))
            else:
                fops.append(win(u, z + 1.0, 3.0, h - 2.6, style="surround", rows=3, cols=2))
    arch.wall(f, T, GFH, zE, fops, T0, rng, panel=5.0, vstep=FH)
    for side, n in (("left", 3), ("right", 3), ("back", bays)):
        Fa = Face(k, side, W, D)
        L = Fa.L
        sops = []
        for li, (name, h) in enumerate(levels[1:], start=1):
            for i in range(n):
                sops.append(win(-L / 2 + (i + 0.5) * L / n, zs[li] + 1.2, 3.0, h - 2.8, style="plain", soot=True))
        arch.wall(Fa, T, GFH, zE, sops, T0, rng, panel=6.0, vstep=FH)
    for li in range(1, len(levels)):
        arch.course(k, "trim", W, D, zs[li], proj=0.35, h=0.6, sides=("front", "left", "right"))
    arch.quoins(k, "wall_b", W, D, GFH, zE, size=1.6, h=1.0)
    if params["balconies"]:
        arch.balcony(f, T, 0.0, zs[2] + 0.2, W - 2.0, depth=1.7, rail_h=3.3)
        if len(levels) > 5:
            arch.balcony(f, T, 0.0, zs[len(levels) - 1] + 0.2, W - 2.0, depth=1.6, rail_h=3.2)
    arch.cornice(k, T, W, D, zE + 0.6, proj=2.0, h=2.8, brackets=True, dentils=True, step=1.1, sides=("front", "left", "right"))
    f.box("soot", 0, zE - 1.4, W, 1.2, 0.03, 0.05)

    # mansard: steep lower slope with dormers, shallow upper slope, flat top
    h1, a1 = 7.0, 7.0 / math.tan(math.radians(70))
    h2, a2 = 2.4, 2.4 / math.tan(math.radians(18))
    x0, y0 = W / 2 + 0.3, D / 2 + 0.3
    arch.frustum(k, "roof", (-x0, x0, -y0, y0, zE + 0.5), (-(x0 - a1), x0 - a1, -(y0 - a1), y0 - a1, zE + 0.5 + h1))
    arch.frustum(k, "roof", (-(x0 - a1), x0 - a1, -(y0 - a1), y0 - a1, zE + 0.5 + h1),
                 (-(x0 - a1 - a2), x0 - a1 - a2, -(y0 - a1 - a2), y0 - a1 - a2, zE + 0.5 + h1 + h2))
    dz = zE + 0.5 + 1.2
    for side in ("front", "back"):
        sgn = -1 if side == "front" else 1
        for u in cs:
            ysl = y0 - (dz + 1.7 - zE - 0.5) / math.tan(math.radians(70)) - 0.9
            Fd = Face(k, side, W, D, oy=(sgn * (ysl - D / 2)))
            arch.wall(Fd, dict(T, wall="roof", wall_b="roof"), dz, dz + 3.6, [win(u, dz + 0.5, 1.9, 2.6, style="hooded", soot=False)], 0.6, None)
            Fd.poly("roof", [(u - 1.6, dz + 3.6), (u + 1.6, dz + 3.6), (u, dz + 5.0)], 0.0, -2.0)
            for sx in (-1, 1):
                Fd.box("roof", u + sx * 1.4, dz + 1.8, 0.25, 3.6, 0.0, 2.0)
            Fd.box("trim", u, dz + 3.7, 3.4, 0.25, 0.3, 0.4)
    for sx in (-1, 1):
        for sy in (-1, 1):
            arch.chimney(k, "wall_b", sx * (W / 2 - 3.0), sy * (D / 4), zE + 6.0, zE + 13.0, 2.6, 1.8, pots=3)
    if params["street"]:
        arch.street_context(k, T, W + 8, D, front_depth=9.0, side=4.0)
    top = zE + 0.5 + h1 + h2 + 8.0
    shots = [
        ("wide", (-W * 1.3, -(D / 2 + W * 2.6), top * 0.55), (0.0, 0.0, top * 0.45), 36.0),
        ("front", (-W * 0.2, -(D / 2 + 22), GFH + 4), (0.0, -D / 2, GFH + 6), 42.0),
        ("mansard", (-W * 0.3, -(D / 2 + 22), zE + 4), (0.0, -D / 2, zE + 4), 45.0),
    ]
    return BuildResult(k.parts, shots, {"W": W, "H": top})
