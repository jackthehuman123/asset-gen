"""Barrel: revolved belly profile, metal hoops, optional lid. Runs inside Blender."""
import math
import random
from typing import Dict

from rbxasset.builders.kit import Kit
from rbxasset.builders.result import BuildResult

TAGS = ("body", "hoops", "lid")


def build(params: Dict, rng: random.Random) -> BuildResult:
    H, R, bulge = params["height"], params["radius"], params["bulge"]
    wall, hoops = params["wall"], params["hoop_count"]
    k = Kit(TAGS)

    def r_at(z):
        return R * (1 + bulge * math.sin(math.pi * z / H))

    zs = [H * j / 8 for j in range(9)]
    outer = [(r_at(z), z) for z in zs]
    if params["open_top"]:
        inner = [(r_at(z) - wall, z) for z in reversed(zs[1:])]
        profile = [(0, 0)] + outer + inner + [(0, zs[1])]
    else:
        profile = [(0, 0)] + outer + [(0, H)]
    k.revolve("body", profile, segments=24)
    if not params["open_top"]:
        k.cyl("lid", R - 0.06, 0.06, (0, 0, H - 0.02), verts=24)
    for i in range(hoops):
        z = H * (0.12 + 0.76 * i / (hoops - 1))
        r = r_at(z)
        k.revolve("hoops", [(r - 0.02, z - 0.07), (r + 0.05, z - 0.07), (r + 0.05, z + 0.07),
                            (r - 0.02, z + 0.07)], segments=24, closed=True)
    s = max(2 * R, H)
    shots = [
        ("wide", (-s * 1.3, -s * 1.9, H * 0.8 + s * 0.3), (0.0, 0.0, H * 0.45), 40.0),
        ("close", (-s * 0.6, -s * 1.2, H * 0.8), (0.0, 0.0, H * 0.55), 50.0),
    ]
    return BuildResult(k.parts, shots, {"W": 2 * R * (1 + bulge), "H": H})
