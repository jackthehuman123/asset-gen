"""Craftsman bungalow: low front gable over a deep porch, tapered columns on brick piers, exposed rafter
tails and knee brackets, lap siding with shingled gable, paired windows. Runs inside Blender."""

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
    "shingle",
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
T0, BH = 0.4, 1.8


def build(params: Dict, rng: random.Random) -> BuildResult:
    W, D, WH, pitch, PD, eave = (
        params[x]
        for x in ("width", "depth", "wall_height", "roof_pitch", "porch_depth", "eave")
    )
    k = Kit(TAGS)
    T = {r: r for r in TAGS}
    zE = BH + WH
    Dw = D - PD  # enclosed depth; the porch is the front PD studs under the same roof
    oy = PD / 2
    k.box("base", (W + 0.3, Dw + 0.3, BH), (0, oy, BH / 2), bevel=0.0)
    k.box("base", (W + 0.6, PD + 0.3, 0.7), (0, -D / 2 + PD / 2, 0.35), bevel=0.0)
    ft = Face(k, "front", W, Dw, oy=oy)
    fops = [arch.Op("door", -2.0, 2.0, BH, BH + 7.2, transom=1.4, hood=False)] + [
        win(u, BH + 2.4, 4.6, 4.2, rows=2, cols=3, style="surround")
        for u in (-9.0, 9.0)
    ]
    arch.wall(ft, T, BH, zE, fops, T0, rng, panel=6.0, vstep=WH)
    ft.box("shingle", 0, zE - 1.2, W, 2.4, 0.06, 0.1)
    for side, L in (("left", Dw), ("right", Dw)):
        ops = [
            win(u, BH + 2.4, 4.6, 4.2, rows=2, cols=3, style="surround")
            for u in (-6.0, 1.0, 8.0)
        ]
        arch.wall(
            Face(k, side, W, Dw, oy=oy), T, BH, zE, ops, T0, rng, panel=6.0, vstep=WH
        )
    arch.wall(
        Face(k, "back", W, Dw, oy=oy),
        T,
        BH,
        zE,
        [
            win(u, BH + 2.4, 4.6, 4.2, rows=2, cols=3, style="surround")
            for u in (-8.0, 0.0, 8.0)
        ],
        T0,
        rng,
        panel=6.0,
    )
    k.box("wall", (W, Dw, 0.2), (0, oy, zE - 0.1), bevel=0.0)

    # front-gabled roof: ridge along y (build along x, rotate), gable fill shingled
    apex, objs = roofs.roof(
        k, {"roof": "roof", "wall": "shingle"}, "gable", D, W, zE, pitch, eave
    )
    roofs.placed(objs, 0.0, 0.0, math.pi / 2)
    tp = math.tan(math.radians(pitch))
    # rafter tails along both eaves and a triple-beam gable decoration over the porch
    for side in (-1, 1):
        x = side * (W / 2 + eave * 0.9)
        n = int(D / 1.6)
        for i in range(n + 1):
            k.box(
                "trim",
                (0.3, 0.9, 0.35),
                (x, -D / 2 + 0.3 + (D - 0.6) * i / n, zE - eave * tp * 0.9 - 0.25),
                bevel=0.0,
            )
        for i in range(0, n + 1, 2):
            k.box(
                "trim",
                (0.3, 0.5, 1.3),
                (side * (W / 2 - 0.1), -D / 2 + 0.3 + (D - 0.6) * i / n, zE - 1.0),
                rot=(0, side * 0.7, 0),
                bevel=0.0,
            )
    ff = Face(k, "front", W, D)
    ff.box("trim", 0, zE + 0.2, W + 2 * eave, 0.3, eave * 0.8, 0.35)
    ff.box("trim", 0, zE + (W / 2) * tp * 0.5, W * 0.62, 0.28, eave * 0.7, 0.3)
    ff.box("trim", 0, zE + (W / 2) * tp * 0.25, W * 0.85, 0.24, eave * 0.7, 0.3)
    k.box(
        "trim",
        (0.3, 0.3, 0.8),
        (0.0, -D / 2 - eave * 0.5, zE + (W / 2) * tp * 0.5 + 0.4),
        bevel=0.0,
    )  # gable vent mark
    # porch: brick piers with tapered columns and a closed rail
    py = -D / 2 + 0.9
    for sx in (-1, 1):
        for ux in (sx * (W / 2 - 1.2), sx * 3.8):
            k.box("brick", (1.7, 1.7, 3.0), (ux, py, 1.5 + 0.35), bevel=0.0)
            k.box("trim", (1.7, 1.7, 0.2), (ux, py, 3.45), bevel=0.0)
            k.cone(
                "trim",
                0.5,
                0.36,
                WH + BH - 3.5 + 0.0,
                (ux, py, 3.5 + (WH + BH - 3.5) / 2 - 0.0),
                verts=4,
                rot=(0, 0, math.pi / 4),
            )
    for sx in (-1, 1):
        a, b = (sx * 3.8, sx * (W / 2 - 1.2))
        lo, hi = min(a, b), max(a, b)
        k.box("wall", (hi - lo - 1.8, 0.35, 2.0), ((lo + hi) / 2, py, 1.8), bevel=0.0)
        k.box("trim", (hi - lo - 1.4, 0.55, 0.22), ((lo + hi) / 2, py, 2.9), bevel=0.0)
    k.box("trim", (W - 2.4, 0.5, 0.9), (0, py, zE - 0.45), bevel=0.0)  # porch beam
    k.box("base", (7.0, 3.0, 0.5), (0.0, -D / 2 + 1.5, 0.25), bevel=0.0)
    arch.chimney(k, "brick", W / 2 + 0.9, oy, 0.0, apex + 1.6, 1.8, 3.2, pots=1)
    if params["street"]:
        arch.street_context(k, T, W + 4, D, front_depth=6.0, side=2.0)
    top = apex + 1.6
    shots = [
        (
            "wide",
            (-W * 0.85, -(D * 1.5 + W * 0.5), top * 1.0),
            (0.0, -D * 0.1, top * 0.4),
            36.0,
        ),
        ("front", (-6, -(D / 2 + 17), BH + 6), (0.0, -D / 2, BH + 5), 42.0),
    ]
    return BuildResult(k.parts, shots, {"W": W + 2 * eave, "H": top})
