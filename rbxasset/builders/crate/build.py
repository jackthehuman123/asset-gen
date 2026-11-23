"""Slatted crate: stacked boards, corner battens, floor, optional lid. Runs inside Blender."""

import random
from typing import Dict

from rbxasset.builders.kit import Kit
from rbxasset.builders.kit_shots import default_shots
from rbxasset.builders.result import BuildResult

TAGS = ("boards", "battens", "lid")
GAP = 0.05


def build(params: Dict, rng: random.Random) -> BuildResult:
    W, D, H, n, t, B = (
        params[x]
        for x in (
            "width",
            "depth",
            "height",
            "board_count",
            "board_thickness",
            "batten_size",
        )
    )
    k = Kit(TAGS)
    bh = (H - (n - 1) * GAP) / n
    for i in range(n):
        z = bh / 2 + i * (bh + GAP)
        for sy in (-1, 1):
            k.box("boards", (W, t, bh), (0, sy * (D / 2 - t / 2), z))
        for sx in (-1, 1):
            k.box("boards", (t, D - 2 * t, bh), (sx * (W / 2 - t / 2), 0, z))
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.box(
                "battens",
                (B, B, H),
                (sx * (W / 2 - B / 2), sy * (D / 2 - B / 2), H / 2),
            )
    k.box("battens", (W - 2 * t, D - 2 * t, 0.08), (0, 0, 0.04))
    if params["lid"]:
        m = 4
        for i in range(m):
            y = -D / 2 + (i + 0.5) * D / m
            k.box("lid", (W + 0.06, D / m - 0.04, t), (0, y, H + t / 2))
    return BuildResult(k.parts, default_shots(W, D, H), {"W": W, "H": H + t})
