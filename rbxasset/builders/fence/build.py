"""Fence run along x: posts, rails, pickets. Runs inside Blender."""

import math
import random
from typing import Dict

from rbxasset.builders.kit import Kit
from rbxasset.builders.result import BuildResult

TAGS = ("posts", "rails", "pickets")


def build(params: Dict, rng: random.Random) -> BuildResult:
    L, H, PS = params["length"], params["height"], params["post_size"]
    n_rail, pw, gap = params["rail_count"], params["picket_width"], params["picket_gap"]
    k = Kit(TAGS)
    count = max(2, int(math.ceil(L / params["post_spacing"])) + 1)
    for i in range(count):
        x = -L / 2 + i * L / (count - 1)
        k.box("posts", (PS, PS, H + 0.1), (x, 0, (H + 0.1) / 2))
        k.box("posts", (PS + 0.08, PS + 0.08, 0.08), (x, 0, H + 0.14), bevel=0.0)
    for r in range(n_rail):
        z = H * (r + 1) / (n_rail + 1)
        k.box("rails", (L, 0.12, 0.2), (0, -PS / 2 + 0.06, z))
    step = pw + gap
    n = max(1, int((L - PS) // step))
    ph = H - 0.12
    y = -(PS / 2 + 0.03)
    for i in range(n):
        x = -((n - 1) * step) / 2 + i * step
        if params["picket_style"] == "pointed":
            k.box(
                "pickets",
                (pw, 0.06, ph - 0.25),
                (x, y, 0.12 + (ph - 0.25) / 2),
                bevel=0.0,
            )
            k.cone(
                "pickets",
                pw * 0.72,
                0.0,
                0.25,
                (x, y, 0.12 + ph - 0.125),
                verts=4,
                rot=(0, 0, math.pi / 4),
            )
        else:
            k.box("pickets", (pw, 0.06, ph), (x, y, 0.12 + ph / 2), bevel=0.0)
    s = max(L, H)
    shots = [
        ("wide", (-L * 0.55, -L * 0.95, H * 1.6), (0.0, 0.0, H * 0.45), 40.0),
        ("close", (-L * 0.2, -s * 0.55, H * 0.9), (-L * 0.25, 0.0, H * 0.55), 50.0),
    ]
    return BuildResult(k.parts, shots, {"W": L, "H": H})
