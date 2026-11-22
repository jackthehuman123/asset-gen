"""Chair / stool / bench: seat, four legs, optional back and arms. Runs inside Blender."""
import random
from typing import Dict

from rbxasset.builders.kit import Kit
from rbxasset.builders.kit_shots import default_shots
from rbxasset.builders.result import BuildResult

TAGS = ("seat", "legs", "back", "arms")
ST = 0.14


def build(params: Dict, rng: random.Random) -> BuildResult:
    SW, SD, SH, BH = params["seat_width"], params["seat_depth"], params["seat_height"], params["back_height"]
    L, style = params["leg_size"], params["back_style"]
    k = Kit(TAGS)
    k.box("seat", (SW, SD, ST), (0, 0, SH - ST / 2), bevel=0.02)
    lx, ly = SW / 2 - L / 2, SD / 2 - L / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.box("legs", (L, L, SH - ST), (sx * lx, sy * ly, (SH - ST) / 2))
    if style != "none":
        for sx in (-1, 1):
            k.box("back", (L, L, BH), (sx * lx, ly, SH + BH / 2))
        k.box("back", (SW, L, 0.16), (0, ly, SH + BH - 0.08))
        inner = SW - 2 * L
        if style == "solid":
            k.box("back", (inner, 0.06, BH - 0.4), (0, ly, SH + 0.2 + (BH - 0.4) / 2))
        else:
            n = params["slat_count"]
            w = inner / (2 * n)
            for i in range(n):
                x = -inner / 2 + inner * (i + 0.5) / n
                k.box("back", (w, 0.05, BH - 0.4), (x, ly, SH + 0.2 + (BH - 0.4) / 2))
    if params["arms"]:
        for sx in (-1, 1):
            k.box("arms", (L, L, 0.9), (sx * lx, -ly, SH + 0.45))
            k.box("arms", (L + 0.06, SD - 0.1, 0.1), (sx * lx, 0, SH + 0.9))
    H = SH + (BH if style != "none" else 0)
    return BuildResult(k.parts, default_shots(SW, SD, H), {"W": SW, "H": H})
