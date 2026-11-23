"""Main-street shopfront block: glazed storefronts with bulkheads, signboards and striped awnings, brick
upper floors with hooded and arched windows, bracketed cornice, fire escape, rooftop parapet."""

import random
from typing import Dict

from rbxasset.builders import arch
from rbxasset.builders.arch import Face, Op, win
from rbxasset.builders.kit import Kit
from rbxasset.builders.result import BuildResult

TAGS = (
    "wall",
    "wall_b",
    "trim",
    "sash",
    "glass",
    "door",
    "sign",
    "awning",
    "awning_b",
    "soot",
    "iron",
    "groove",
    "roof",
    "ground",
    "curb",
    "road",
)
T0, GFH = 0.5, 13.0


def build(params: Dict, rng: random.Random) -> BuildResult:
    W, D, F, FH, shops = (
        params[x] for x in ("width", "depth", "floors", "floor_height", "shops")
    )
    k = Kit(TAGS)
    T = {r: r for r in TAGS}
    zE = GFH + (F - 1) * FH
    sw = W / shops
    sc = [-W / 2 + (i + 0.5) * sw for i in range(shops)]
    f = Face(k, "front", W, D)
    # ground floor: a storefront per shop, a pilaster between them, signboard above
    ops = []
    for i, u in enumerate(sc):
        ops.append(
            Op(
                "shop",
                u - sw / 2 + 1.0,
                u + sw / 2 - 1.0,
                0.0,
                GFH - 3.4,
                bulkhead=1.3,
                panes=3,
                door_u=u + sw * 0.28,
            )
        )
    arch.wall(f, T, 0.0, GFH, ops, T0, rng, panel=5.0, vstep=GFH)
    for i in range(shops + 1):
        u = -W / 2 + i * sw
        f.box("wall_b", u, GFH / 2, 1.5, GFH, 0.5, 0.6)
    for i, u in enumerate(sc):
        f.box("sign", u, GFH - 1.8, sw - 2.4, 1.9, 0.35, 0.35)
        f.box("trim", u, GFH - 0.55, sw - 1.9, 0.3, 0.5, 0.5)
        if params["awnings"]:
            Ta = dict(T, awning="awning" if i % 2 == 0 else "awning_b")
            arch.awning(
                f,
                Ta,
                u - sw / 2 + 1.3,
                u + sw / 2 - 1.3,
                GFH - 3.0,
                depth=3.0,
                drop=1.7,
            )
    for side in ("left", "right"):
        Fa = Face(k, side, W, D)
        arch.wall(
            Fa,
            T,
            0.0,
            GFH,
            [
                Op(
                    "shop",
                    -D / 2 + 2.0,
                    -D / 2 + 9.0,
                    0.0,
                    GFH - 3.4,
                    bulkhead=1.3,
                    panes=2,
                )
            ],
            T0,
            rng,
            panel=6.0,
        )
    arch.wall(
        Face(k, "back", W, D),
        T,
        0.0,
        GFH,
        [Op("door", -2.0, 2.0, 0.0, 7.4, hood=False)],
        T0,
        rng,
        panel=6.0,
    )
    # upper floors
    uops = []
    for fl in range(1, F):
        z = GFH + (fl - 1) * FH
        for i, u in enumerate(sc):
            for du in (-sw * 0.22, sw * 0.22):
                style = "hooded" if (i + fl) % 2 == 0 else "pediment"
                uops.append(
                    win(
                        u + du,
                        z + 1.9,
                        3.2,
                        6.4,
                        style=style,
                        rows=3,
                        cols=2,
                        ac=(rng.random() < 0.3),
                    )
                )
    arch.wall(f, T, GFH, zE, uops, T0, rng, panel=5.0, vstep=FH, variant=0.3)
    for side, n in (("left", 3), ("right", 3), ("back", 4)):
        Fa = Face(k, side, W, D)
        L = Fa.L
        sops = [
            win(
                -L / 2 + (i + 0.5) * L / n,
                GFH + (fl - 1) * FH + 1.9,
                3.0,
                6.0,
                style="plain",
            )
            for fl in range(1, F)
            for i in range(n)
        ]
        arch.wall(Fa, T, GFH, zE, sops, T0, rng, panel=6.0, vstep=FH, variant=0.3)
    for fl in range(1, F):
        arch.course(
            k, "trim", W, D, GFH + (fl - 1) * FH, proj=0.3, h=0.5, sides=("front",)
        )
        f.box("soot", 0, GFH + (fl - 1) * FH - 0.9, W, 1.0, 0.03, 0.05)
    arch.cornice(
        k,
        T,
        W,
        D,
        zE + 1.2,
        proj=1.8,
        h=2.6,
        brackets=True,
        dentils=True,
        step=1.4,
        sides=("front",),
    )
    f.box("soot", 0, zE - 1.6, W, 1.0, 0.03, 0.05)
    k.box("wall", (W, T0, 2.2), (0, -(D / 2 - T0 / 2), zE + 1.1), bevel=0.0)
    k.box("wall", (W, T0, 2.2), (0, D / 2 - T0 / 2, zE + 1.1), bevel=0.0)
    for sx in (-1, 1):
        k.box(
            "wall",
            (T0, D - 2 * T0, 2.2),
            (sx * (W / 2 - T0 / 2), 0, zE + 1.1),
            bevel=0.0,
        )
    k.box("trim", (W + 0.4, 0.8, 0.3), (0, -(D / 2 - 0.2), zE + 2.3), bevel=0.0)
    k.box("roof", (W - 0.2, D - 0.2, 0.4), (0, 0, zE + 0.2), bevel=0.0)
    if params["fire_escape"]:
        arch.fire_escape(
            Face(k, "right", W, D), T, 3.0, GFH, F - 1, FH, w=5.0, depth=1.8
        )
    if params["street"]:
        arch.street_context(k, T, W + 8, D, front_depth=9.0, side=4.0)
    top = zE + 2.6
    shots = [
        (
            "wide",
            (-W * 0.55, -(D / 2 + W * 0.95), top * 0.5),
            (0.0, 0.0, top * 0.45),
            36.0,
        ),
        ("front", (sc[0] + 3, -(D / 2 + 20), 6), (sc[0] + 4, -D / 2, 6), 42.0),
        ("cornice", (-4, -(D / 2 + 17), zE - 2), (0.0, -D / 2, zE), 48.0),
    ]
    return BuildResult(k.parts, shots, {"W": W, "H": top})
