"""Straight stair flight rising along +y. Runs inside Blender."""

import math
import random
from typing import Dict

from rbxasset.builders.kit import Kit
from rbxasset.builders.result import BuildResult

TAGS = ("treads", "risers", "stringers", "rail")
NOSING, RAIL_H = 0.1, 2.4


def build(params: Dict, rng: random.Random) -> BuildResult:
    N, rise, run, W, tt = (
        params[x] for x in ("steps", "rise", "run", "width", "tread_thickness")
    )
    k = Kit(TAGS)
    y0 = -N * run / 2
    for i in range(N):
        yc = y0 + i * run + run / 2
        k.box(
            "treads",
            (W, run + NOSING, tt),
            (0, yc - NOSING / 2, (i + 1) * rise - tt / 2),
            bevel=0.015,
        )
        if params["risers"]:
            k.box(
                "risers",
                (W - 0.02, 0.05, rise - tt),
                (0, y0 + i * run + 0.025, i * rise + (rise - tt) / 2),
                bevel=0.0,
            )
        if params["stringers"]:
            for sx in (-1, 1):
                k.box(
                    "stringers",
                    (0.15, run, (i + 1) * rise - tt),
                    (sx * (W / 2 + 0.075), yc, ((i + 1) * rise - tt) / 2),
                    bevel=0.0,
                )
    top = N * rise
    if params["handrail"]:
        ya, yb = y0 + 0.15, y0 + N * run - 0.15
        za, zb = rise + RAIL_H / 2, N * rise + RAIL_H / 2
        for sx in (-1, 1):
            x = sx * (W / 2 + 0.075)
            k.box("rail", (0.12, 0.12, RAIL_H), (x, ya, za), bevel=0.0)
            k.box("rail", (0.12, 0.12, RAIL_H), (x, yb, zb), bevel=0.0)
            length = math.hypot(yb - ya, zb - za)
            k.box(
                "rail",
                (0.1, length, 0.1),
                (x, (ya + yb) / 2, (za + zb) / 2 + RAIL_H / 2 - 0.05),
                rot=(math.atan2(zb - za, yb - ya), 0, 0),
                bevel=0.0,
            )
        top += RAIL_H
    s = max(W, N * run, top)
    shots = [
        ("wide", (-s * 1.3, -s * 1.8, top * 0.9 + 1.5), (0.0, 0.0, top * 0.5), 40.0),
        (
            "close",
            (-s * 0.6, -N * run * 0.9 - 1.0, top * 0.5 + 1.0),
            (0.0, y0 + N * run * 0.3, top * 0.35),
            50.0,
        ),
    ]
    return BuildResult(k.parts, shots, {"W": W, "H": top})
