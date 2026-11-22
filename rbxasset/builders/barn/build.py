"""Barn: gambrel roof, big double doors on the gable end, optional hayloft door. Runs inside Blender."""
import math
import random
from typing import Dict

from rbxasset.builders import facade, roofs
from rbxasset.builders.kit import Kit
from rbxasset.builders.result import BuildResult

TAGS = ("foundation", "walls", "trim", "roof", "door")
T, PL = 0.4, 1.0


def build(params: Dict, rng: random.Random) -> BuildResult:
    W, L, WH = params["width"], params["length"], params["wall_height"]
    dw, dh = params["door_width"], params["door_height"]
    k = Kit(TAGS)
    tags = {"wall": "walls", "trim": "trim", "glazing": "trim", "door": "door"}
    k.box("foundation", (W + 0.2, L + 0.2, PL), (0, 0, PL / 2), bevel=0.0)
    zE = PL + WH
    front = [("big_door", -dw / 2, dw / 2, PL, PL + dh)]
    if params["loft_door"]:
        front.append(("door", -1.6, 1.6, zE - 4.5, zE - 1.0))
    side = [("window", u0, u1, PL + 5.0, PL + 7.4) for (u0, u1) in facade.evenly(L, 2, 2.0)]
    ops = {"front": front, "back": [], "left": side, "right": side}
    for s in facade.SIDES:
        facade.wall_with_openings(k, tags, s, W, L, T, PL, zE, ops[s])
    k.box("walls", (W - 0.1, L - 0.1, 0.2), (0, 0, zE - 0.1), bevel=0.0)
    apex, objs = roofs.roof(k, {"roof": "roof", "wall": "walls"}, "gambrel", L, W, zE, 30.0, params["eave"])
    Kit.rotate_z(objs, math.pi / 2)
    s = max(W, L, apex)
    shots = [
        ("wide", (-W * 1.2 - 6, -(L * 0.8 + W), apex * 0.6), (0.0, 0.0, apex * 0.4), 38.0),
        ("front", (-W * 0.5, -(L / 2 + 16), PL + 6), (0.0, -L / 2, PL + 6), 45.0),
    ]
    return BuildResult(k.parts, shots, {"W": W, "H": apex})
