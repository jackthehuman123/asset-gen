"""Lamp post: flared base, pole, optional arm, lantern or globe head. Runs inside Blender.
The origin is the pole base, so the asset is not x-centred when it has an arm."""
import math
import random
from typing import Dict

from rbxasset.builders.kit import Kit
from rbxasset.builders.result import BuildResult

TAGS = ("base", "pole", "arm", "head", "lens")


def build(params: Dict, rng: random.Random) -> BuildResult:
    H, BR, BH = params["height"], params["base_radius"], params["base_height"]
    PR, AL, HR = params["pole_radius"], params["arm_length"], params["head_radius"]
    k = Kit(TAGS)
    k.revolve("base", [(0, 0), (BR, 0), (BR, 0.18), (BR * 0.62, BH * 0.55), (PR * 1.7, BH * 0.8),
                       (PR * 1.25, BH), (0, BH)], segments=20)
    head_h = HR * 2.2
    top = H - head_h
    k.cone("pole", PR * 1.15, PR, top - BH, (0, 0, BH + (top - BH) / 2), verts=14)
    hx = AL
    if AL > 0:
        k.cyl("arm", PR * 0.8, AL, (AL / 2, 0, top - PR), rot=(0, math.pi / 2, 0), verts=10)
        k.sphere("arm", PR * 1.1, (0, 0, top - PR))
    k.box("head", (HR * 1.5, HR * 1.5, 0.07), (hx, 0, top + 0.035), bevel=0.0)
    if params["head_style"] == "lantern":
        k.box("lens", (HR * 1.3, HR * 1.3, head_h * 0.62), (hx, 0, top + head_h * 0.38), bevel=0.0)
        k.cone("head", HR * 1.15, HR * 0.15, head_h * 0.3, (hx, 0, H - head_h * 0.15), verts=4,
               rot=(0, 0, math.pi / 4))
    else:
        k.sphere("lens", HR, (hx, 0, top + head_h * 0.45))
        k.cone("head", HR * 0.9, HR * 0.1, head_h * 0.22, (hx, 0, H - head_h * 0.11), verts=12)
    shots = [
        ("wide", (-H * 0.9, -H * 1.5, H * 0.5), (0.0, 0.0, H * 0.45), 40.0),
        ("close", (-H * 0.25 + hx, -H * 0.45, H * 0.9), (hx, 0.0, H * 0.9), 50.0),
    ]
    return BuildResult(k.parts, shots, {"W": max(2 * BR, hx + HR), "H": H})
