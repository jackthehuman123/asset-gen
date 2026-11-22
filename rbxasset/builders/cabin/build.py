"""Log cabin: stacked log courses with notched-corner overhang, gable roof, porch, stone chimney."""
import math
import random
from typing import Dict

from rbxasset.builders import facade, roofs
from rbxasset.builders.kit import Kit
from rbxasset.builders.result import BuildResult

TAGS = ("foundation", "logs", "trim", "roof", "door", "glazing", "chimney")
ZB = 0.6


def _gaps(L, ops, z_lo, z_hi):
    cover = sorted((o[1], o[2]) for o in ops if o[3] < z_hi and o[4] > z_lo)
    out, cur = [], -L / 2
    for a, b in cover + [(L / 2, L / 2)]:
        if a - cur > 1e-6:
            out.append((cur, a))
        cur = max(cur, b)
    return out


def build(params: Dict, rng: random.Random) -> BuildResult:
    W, D, n, R = params["width"], params["depth"], params["log_courses"], params["log_radius"]
    k = Kit(TAGS)
    tags = {"wall": "logs", "trim": "trim", "glazing": "glazing", "door": "door"}
    step = 2 * R * 0.88
    zE = ZB + n * step + R * 0.2
    k.box("foundation", (W - 0.4, D - 0.4, ZB), (0, 0, ZB / 2), bevel=0.0)
    wz = ZB + 3.0
    ops = {
        "front": [("door", -1.5, 1.5, ZB + 0.1, ZB + 6.6), ("window", -W * 0.3 - 1.1, -W * 0.3 + 1.1, wz, wz + 3.0),
                  ("window", W * 0.3 - 1.1, W * 0.3 + 1.1, wz, wz + 3.0)],
        "back": [("window", -W * 0.25 - 1.1, -W * 0.25 + 1.1, wz, wz + 3.0),
                 ("window", W * 0.25 - 1.1, W * 0.25 + 1.1, wz, wz + 3.0)],
        "left": [("window", -1.1, 1.1, wz, wz + 3.0)],
        "right": [("window", -1.1, 1.1, wz, wz + 3.0)],
    }
    ext = R + 0.25
    for i in range(n):
        z = ZB + R + i * step
        for side, sgn, L in (("front", -1, W), ("back", 1, W)):
            for a, b in _gaps(L, ops[side], z - R, z + R):
                a -= ext if a <= -L / 2 + 1e-6 else 0
                b += ext if b >= L / 2 - 1e-6 else 0
                k.cyl("logs", R, b - a, ((a + b) / 2, sgn * (D / 2 - R), z), rot=(0, math.pi / 2, 0), verts=12)
        zs = z + step / 2
        for side, sgn, L in (("left", -1, D), ("right", 1, D)):
            for a, b in _gaps(L, ops[side], zs - R, zs + R):
                a -= ext if a <= -L / 2 + 1e-6 else 0
                b += ext if b >= L / 2 - 1e-6 else 0
                k.cyl("logs", R, b - a, (sgn * (W / 2 - R), (a + b) / 2, zs), rot=(math.pi / 2, 0, 0), verts=12)
    for side in facade.SIDES:
        for op in ops[side]:
            facade.fit_opening(k, tags, side, W, D, 2 * R, op)
    apex, _ = roofs.roof(k, {"roof": "roof", "wall": "logs"}, "gable", W, D, zE,
                         params["roof_pitch"], params["eave"])
    if params["chimney"]:
        top = apex + 1.0
        k.box("chimney", (1.6, 1.6, top - ZB), (W * 0.27, 0, ZB + (top - ZB) / 2), bevel=0.0)
    PD = params["porch_depth"]
    if params["porch"]:
        pw = W * 0.55
        k.box("foundation", (pw, PD, ZB + 0.2), (0, -(D / 2 + PD / 2), (ZB + 0.2) / 2), bevel=0.0)
        ph = 6.8
        for sgn in (-1, 1):
            k.cyl("trim", 0.22, ph, (sgn * (pw / 2 - 0.3), -(D / 2 + PD - 0.3), ZB + 0.2 + ph / 2), verts=10)
        k.box("roof", (pw + 0.8, PD + 0.8, 0.22), (0, -(D / 2 + PD / 2 - 0.2), ZB + 0.2 + ph + 0.11), bevel=0.0)
    s = max(W, D, apex)
    shots = [
        ("wide", (-W * 0.9, -(D * 1.6 + W * 0.8), apex * 0.8 + 2), (0.0, 0.0, apex * 0.45), 38.0),
        ("front", (-4.0, -(D / 2 + PD + 8), ZB + 5), (0.0, -D / 2, ZB + 4), 45.0),
    ]
    return BuildResult(k.parts, shots, {"W": W, "H": apex})
