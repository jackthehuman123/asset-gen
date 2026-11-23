"""Tudor revival: plaster panels framed in dark timber studs and braces, jettied upper floor,
steep cross-gabled slate roof, tall brick chimney, leaded windows. Runs inside Blender."""

import math
import random
from typing import Dict

from rbxasset.builders import arch, roofs
from rbxasset.builders.arch import Face, win
from rbxasset.builders.kit import Kit
from rbxasset.builders.result import BuildResult

TAGS = (
    "base",
    "wall",
    "wall_b",
    "timber",
    "trim",
    "sash",
    "glass",
    "door",
    "soot",
    "iron",
    "brick",
    "roof",
    "ground",
    "curb",
    "road",
)
T0, BH = 0.4, 2.4


def build(params: Dict, rng: random.Random) -> BuildResult:
    W, D, FH, pitch, J = (
        params[x] for x in ("width", "depth", "floor_height", "roof_pitch", "jetty")
    )
    k = Kit(TAGS)
    T = {r: r for r in TAGS}
    TB = dict(T, wall="base", wall_b="base")
    z1, zE = BH + FH, BH + 2 * FH
    ww, wd = 11.0, 3.5
    wx, oyw = -W / 2 + ww / 2 + 1.0, -D / 2 - wd / 2
    for side in ("front", "back", "left", "right"):
        arch.wall(Face(k, side, W, D), TB, 0.0, BH, [], T0, rng, panel=6.0)
    k.box("base", (ww + 0.2, wd + 0.2, BH), (wx, oyw, BH / 2), bevel=0.0)

    door_u = W / 2 - 6.0
    lead = dict(rows=4, cols=3, style="surround")
    # ground floor (plaster + timber)
    gops = [
        arch.Op("door", door_u - 1.8, door_u + 1.8, BH, BH + 7.4, hood=True),
        win(door_u + 6.5, BH + 2.4, 4.2, 4.6, **lead),
        win(door_u - 7.0, BH + 2.4, 3.6, 4.6, **lead),
    ]
    f0 = Face(k, "front", W, D)
    arch.wall(f0, T, BH, z1, gops, T0, rng, panel=6.0, vstep=FH)
    arch.timber(f0, T, BH, z1, gops, spacing=3.8, braces=False)
    # upper floor, jettied forward by J
    f1 = Face(k, "front", W, D, oy=-J)
    uops = [
        win(u, z1 + 2.0, 3.8, 4.8, **lead) for u in (-4.0, door_u - 2.0, door_u + 4.5)
    ]
    arch.wall(f1, T, z1, zE, uops, T0, rng, panel=6.0, vstep=FH)
    arch.timber(f1, T, z1, zE, uops, spacing=3.4)
    for i in range(int(W / 2.4)):
        f1.box(
            "timber",
            -W / 2 + 1.2 + i * 2.4,
            z1 - 0.35,
            0.5,
            0.7,
            0.0 + J * 0.0 + 0.9,
            J + 0.3,
        )
    f1.box("timber", 0, z1 - 0.12, W, 0.3, 0.2, J + 0.3)
    for side in ("left", "right"):
        Fa = Face(k, side, W, D + J, oy=-J / 2)
        arch.wall(
            Face(k, side, W, D),
            T,
            BH,
            z1,
            [win(-3.0, BH + 2.4, 3.6, 4.6, **lead)],
            T0,
            rng,
            panel=6.0,
        )
        sops = [
            win(-3.0, z1 + 2.0, 3.6, 4.8, **lead),
            win(4.0, z1 + 2.0, 3.6, 4.8, **lead),
        ]
        arch.wall(Fa, T, z1, zE, sops, T0, rng, panel=6.0)
        arch.timber(Fa, T, z1, zE, sops, spacing=3.6)
    bops = [
        win(u, BH + f * FH + 2.2, 3.6, 4.8, **lead)
        for f in range(2)
        for u in (-7.0, 0.0, 7.0)
    ]
    arch.wall(Face(k, "back", W, D), T, BH, zE, bops, T0, rng, panel=6.0)

    # front cross-gable wing (plaster with timber gable)
    fw = Face(k, "front", ww, wd, ox=wx, oy=oyw)
    wops = [win(0.0, BH + 2.4, 4.4, 4.6, **lead), win(0.0, z1 + 2.0, 4.4, 4.8, **lead)]
    arch.wall(fw, T, BH, zE, wops, T0, rng, panel=6.0)
    arch.timber(fw, T, z1, zE, wops, spacing=3.6)
    for side in ("left", "right"):
        arch.wall(
            Face(k, side, ww, wd, ox=wx, oy=oyw), T, BH, zE, [], T0, rng, panel=6.0
        )

    apex, _ = roofs.roof(
        k, {"roof": "roof", "wall": "wall"}, "gable", W, D + J, zE, pitch, 0.9
    )
    Lr = wd + J + D * 0.4
    wapex, objs = roofs.roof(
        k, {"roof": "roof", "wall": "wall"}, "gable", Lr, ww, zE, pitch + 3, 0.8
    )
    roofs.placed(objs, wx, -D / 2 - wd + Lr / 2 - J * 0, math.pi / 2)
    arch.gable_timber(fw, T, ww, zE, ww / 2 * math.tan(math.radians(pitch + 3)), n=5)
    for side in ("left", "right"):
        arch.gable_timber(
            Face(k, side, W, D + J, oy=-J / 2),
            T,
            D + J,
            zE,
            (D + J) / 2 * math.tan(math.radians(pitch)),
            n=7,
        )
    arch.chimney(k, "brick", W * 0.3, -D * 0.1, zE, apex + 2.5, 2.4, 2.0, pots=3)
    # entrance hood on timber brackets
    hx = door_u
    k.box(
        "roof",
        (5.4, 2.6, 0.25),
        (hx, -(D / 2 + 1.3), BH + 8.4),
        rot=(0.25, 0, 0),
        bevel=0.0,
    )
    for sgn in (-1, 1):
        k.box(
            "timber",
            (0.25, 0.25, 2.2),
            (hx + sgn * 2.5, -(D / 2 + 2.4), BH + 7.4),
            bevel=0.0,
        )
    if params["street"]:
        arch.street_context(k, T, W + 4, D + 2 * wd, front_depth=6.0, side=2.0)
    top = apex + 2.5
    shots = [
        (
            "wide",
            (-W * 0.95, -(D * 1.6 + W * 0.8), top * 0.65),
            (0.0, -D * 0.1, top * 0.42),
            36.0,
        ),
        (
            "front",
            (door_u - 6, -(D / 2 + wd + 16), BH + 8),
            (door_u - 2, -D / 2, BH + 8),
            42.0,
        ),
    ]
    return BuildResult(k.parts, shots, {"W": W, "H": top})
