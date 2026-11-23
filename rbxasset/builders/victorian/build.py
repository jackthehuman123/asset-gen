"""Victorian (Queen Anne): corner turret, front cross-gable with fishscale shingles, wrap porch with
turned posts and balusters, side bay, steep roofs, brick chimneys. Runs inside Blender."""
import math
import random
from typing import Dict

from rbxasset.builders import arch, roofs
from rbxasset.builders.arch import Face, win
from rbxasset.builders.kit import Kit
from rbxasset.builders.result import BuildResult

TAGS = ("base", "wall", "wall_b", "shingle", "trim", "sash", "glass", "door", "soot", "iron", "brick",
        "roof", "ground", "curb", "road")
T0, BH = 0.4, 2.2


def build(params: Dict, rng: random.Random) -> BuildResult:
    W, D, FH, pitch = params["width"], params["depth"], params["floor_height"], params["roof_pitch"]
    k = Kit(TAGS)
    T = {r: r for r in TAGS}
    zE = BH + 2 * FH
    ww, wd = 11.0, 5.0
    wx, oyw = -W / 2 + ww / 2 + 0.5, -D / 2 - wd / 2
    k.box("base", (W + 0.3, D + 0.3, BH), (0, 0, BH / 2), bevel=0.0)
    k.box("base", (ww + 0.3, wd + 0.3, BH), (wx, oyw, BH / 2), bevel=0.0)
    door_u = W / 2 - 6.5

    front = Face(k, "front", W, D)
    fops = [arch.Op("door", door_u - 1.7, door_u + 1.7, BH, BH + 7.6, transom=1.6),
            win(door_u + 6.5, BH + 2.0, 3.0, 6.0, style="surround"),
            win(door_u, BH + FH + 2.0, 3.2, 6.2, style="pediment"),
            win(door_u + 6.5, BH + FH + 2.0, 3.0, 6.2, style="hooded")]
    arch.wall(front, T, BH, zE, fops, T0, rng, panel=5.0, vstep=FH)
    front.box("shingle", 0, BH + FH + 0.2, W, 1.4, 0.05, 0.08)
    for u in (door_u - 1.9 - 4.0,):
        pass
    side_ops = lambda L, n: [win(-L / 2 + (i + 0.5) * L / n, BH + f * FH + 2.0, 3.0, 6.0, style="surround",
                                 shutters=False) for f in range(2) for i in range(n)]
    arch.wall(Face(k, "back", W, D), T, BH, zE, side_ops(W, 4), T0, rng, panel=5.0, vstep=FH)
    arch.wall(Face(k, "left", W, D), T, BH, zE, side_ops(D, 3), T0, rng, panel=5.0, vstep=FH)
    right = Face(k, "right", W, D)
    rops = [win(u, BH + FH + 2.0, 3.0, 6.0, style="surround") for u in (-5.0, 3.0)]
    arch.wall(right, T, BH, zE, rops, T0, rng, panel=5.0, vstep=FH)
    arch.oriel(right, T, -4.0, BH + 1.2, 8.0, 6.8, depth=2.2)

    # front cross-gable wing with a ground-floor bay and shingled gable
    fw = Face(k, "front", ww, wd, ox=wx, oy=oyw)
    arch.wall(fw, T, BH, zE, [win(-2.6, BH + FH + 2.0, 2.8, 6.0, style="hooded"),
                              win(2.6, BH + FH + 2.0, 2.8, 6.0, style="hooded")], T0, rng, panel=5.0, vstep=FH)
    arch.oriel(fw, T, 0.0, BH + 1.2, 7.0, 6.8, depth=2.0)
    for side in ("left", "right"):
        arch.wall(Face(k, side, ww, wd, ox=wx, oy=oyw), T, BH, zE,
                  [win(0.0, BH + f * FH + 2.0, 2.6, 6.0, style="surround") for f in range(2)], T0, rng, panel=5.0, vstep=FH)
    fw.box("shingle", 0, BH + FH + 0.2, ww, 1.4, 0.05, 0.08)

    # roofs: main gable along x, wing gable along y
    apex, _ = roofs.roof(k, {"roof": "roof", "wall": "wall"}, "gable", W, D, zE, pitch, 1.6)
    Lr = wd + D * 0.4
    wapex, objs = roofs.roof(k, {"roof": "roof", "wall": "shingle"}, "gable", Lr, ww, zE, pitch + 4, 1.2)
    roofs.placed(objs, wx, -D / 2 - wd + Lr / 2, math.pi / 2)
    arch.gable_timber(fw, dict(T, timber="trim"), ww, zE, ww / 2 * math.tan(math.radians(pitch + 4)), n=4, th=0.12)
    arch.chimney(k, "brick", W * 0.28, 0.0, zE, apex + 1.8, 1.8, 1.8)
    arch.chimney(k, "brick", -W * 0.32, D * 0.1, zE, apex + 1.2, 1.6, 1.6)

    # turret at the wing's front-right corner
    if params["turret"]:
        arch.turret(k, T, wx + ww / 2, -(D / 2 + wd), BH, 2.9, 2 * FH + 0.6, 7.5)

    # wrap porch: deck, turned posts, balusters, shed roof, steps
    if params["porch"]:
        x0, x1 = wx + ww / 2 + 3.2, W / 2 + 0.6
        pw = x1 - x0
        py = -(D / 2 + 3.2)
        k.box("base", (pw, 6.4, 0.5), ((x0 + x1) / 2, py, BH - 0.25), bevel=0.0)
        n = int(pw // 4.2)
        for i in range(n + 1):
            x = x0 + 0.5 + (pw - 1.0) * i / n
            arch.post(k, "trim", x, py - 2.9, BH, BH + FH * 0.82)
            k.box("trim", (0.9, 0.2, 0.8), (x, py - 2.9, BH + FH * 0.82 - 0.4), bevel=0.0)
        for i in range(int((pw - 1) / 0.55)):
            k.box("trim", (0.12, 0.12, 2.3), (x0 + 0.6 + i * 0.55, py - 2.9, BH + 1.2), bevel=0.0)
        k.box("trim", (pw, 0.2, 0.22), ((x0 + x1) / 2, py - 2.9, BH + 2.45), bevel=0.0)
        k.box("trim", (pw, 0.2, 0.22), ((x0 + x1) / 2, py - 2.9, BH + 0.3), bevel=0.0)
        k.box("roof", (pw + 1.2, 7.4, 0.3), ((x0 + x1) / 2, py - 0.5, BH + FH * 0.82 + 0.25), rot=(-0.12, 0, 0), bevel=0.0)
        k.box("trim", (pw + 1.2, 0.3, 0.7), ((x0 + x1) / 2, py - 4.1, BH + FH * 0.82 - 0.2), bevel=0.0)
        for i in range(3):
            k.box("base", (4.0 + 0.6 * i, 0.8, 0.5 - 0.17 * i), (door_u, -(D / 2 + 6.4 + 0.4 + i * 0.8) + 0.0, (0.5 - 0.17 * i) / 2 + BH - 0.5 + 0.17 * i * 0), bevel=0.0)
    if params["street"]:
        arch.street_context(k, T, W + 6, D + 2 * wd + 6.4, front_depth=6.0, side=2.0)
    top = apex + 2.0
    shots = [
        ("wide", (-W * 0.9, -(D * 1.5 + W * 0.8), top * 0.7), (0.0, -D * 0.2, top * 0.45), 36.0),
        ("front", (wx + 6, -(D / 2 + wd + 18), BH + 8), (wx + 4, -(D / 2 + wd), BH + 10), 42.0),
        ("turret", (wx - 5, -(D / 2 + wd + 12), BH + 2 * FH), (wx + ww / 2, -(D / 2 + wd), BH + 2 * FH), 45.0),
    ]
    return BuildResult(k.parts, shots, {"W": W, "H": top})
