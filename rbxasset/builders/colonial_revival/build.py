"""Colonial Revival / Georgian: symmetrical brick block, five-bay front with shuttered six-over-six
windows, pedimented portico on columns, dentil cornice, end chimneys, slate gable roof."""

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
    "trim",
    "sash",
    "glass",
    "door",
    "shutter",
    "soot",
    "iron",
    "brick",
    "roof",
    "ground",
    "curb",
    "road",
)
T0, BH = 0.45, 2.2


def build(params: Dict, rng: random.Random) -> BuildResult:
    W, D, FH, pitch, bays = (
        params[x] for x in ("width", "depth", "floor_height", "roof_pitch", "bays")
    )
    k = Kit(TAGS)
    T = dict({r: r for r in TAGS}, wall="wall")
    zE = BH + 2 * FH
    k.box("base", (W + 0.3, D + 0.3, BH), (0, 0, BH / 2), bevel=0.0)
    arch.rustication(k, "iron", W, D, 0.3, BH, h=1.1)
    f = Face(k, "front", W, D)
    cs = [-W / 2 + (i + 0.5) * W / bays for i in range(bays)]
    mid = bays // 2
    ops = []
    for fl in range(2):
        z = BH + fl * FH
        for i, u in enumerate(cs):
            if fl == 0 and i == mid:
                ops.append(
                    arch.Op(
                        "door", u - 2.2, u + 2.2, z, z + 8.4, transom=2.0, hood=True
                    )
                )
            elif fl == 1 and i == mid:
                ops.append(
                    win(
                        u,
                        z + 1.8,
                        3.4,
                        6.8,
                        style="hooded",
                        shutters=False,
                        rows=3,
                        cols=2,
                    )
                )
            else:
                ops.append(
                    win(
                        u,
                        z + 1.6,
                        3.2,
                        7.0 if fl == 0 else 6.4,
                        style="plain",
                        shutters=True,
                        rows=3,
                        cols=2,
                    )
                )
    arch.wall(f, T, BH, zE, ops, T0, rng, panel=5.0, vstep=FH)
    for fl in range(1, 2):
        arch.course(k, "trim", W, D, BH + fl * FH, proj=0.3, h=0.5, sides=("front",))
    for side, n in (("left", 2), ("right", 2), ("back", bays)):
        Fa = Face(k, side, W, D)
        L = Fa.L
        sops = [
            win(
                -L / 2 + (i + 0.5) * L / n,
                BH + fl * FH + 1.8,
                3.2,
                6.4,
                style="plain",
                shutters=False,
            )
            for fl in range(2)
            for i in range(n)
        ]
        arch.wall(Fa, T, BH, zE, sops, T0, rng, panel=5.0, vstep=FH)
    arch.quoins(k, "wall_b", W, D, BH, zE, size=1.5, h=0.9)
    arch.cornice(
        k,
        T,
        W,
        D,
        zE + 0.4,
        proj=1.5,
        h=2.2,
        brackets=False,
        dentils=True,
        sides=("front", "back"),
    )
    apex, _ = roofs.roof(
        k, {"roof": "roof", "wall": "wall"}, "gable", W, D, zE + 0.2, pitch, 0.8
    )
    for sx in (-1, 1):
        arch.chimney(
            k, "brick", sx * (W / 2 - 2.0), 0.0, zE, apex + 1.8, 2.6, 3.0, pots=2
        )
    if params["portico"]:
        arch.portico(
            f, T, cs[mid], BH, 9.4, 4.5, FH + 1.2, columns=4, pediment=True, steps=3
        )
    if params["street"]:
        arch.street_context(k, T, W + 6, D + 4.5, front_depth=6.0, side=3.0)
    top = apex + 2.0
    shots = [
        (
            "wide",
            (-W * 0.8, -(D * 1.5 + W * 0.7), top * 0.7),
            (0.0, -D * 0.1, top * 0.42),
            36.0,
        ),
        (
            "front",
            (cs[mid] - 5, -(D / 2 + 20), BH + 8),
            (cs[mid], -D / 2, BH + 8),
            42.0,
        ),
    ]
    return BuildResult(k.parts, shots, {"W": W, "H": top})
