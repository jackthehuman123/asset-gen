"""Detached house: foundation, windowed walls, one of four roof forms, optional porch and chimney."""
import random
from typing import Dict

from rbxasset.builders import facade, roofs
from rbxasset.builders.kit import Kit
from rbxasset.builders.result import BuildResult

TAGS = ("foundation", "walls", "trim", "roof", "door", "glazing", "chimney")
WALL_T, WIN_W, WIN_H, SILL, DOOR_W, DOOR_H = 0.3, 2.2, 3.2, 2.8, 3.0, 6.4


def build(params: Dict, rng: random.Random) -> BuildResult:
    W, D, S, SH, FH = (params[x] for x in ("width", "depth", "storeys", "storey_height", "foundation_height"))
    bays = params["bays"]
    k = Kit(TAGS)
    tags = {"wall": "walls", "trim": "trim", "glazing": "glazing", "door": "door"}
    k.box("foundation", (W + 0.2, D + 0.2, FH), (0, 0, FH / 2), bevel=0.0)
    zE = FH + S * SH
    door_i = bays // 2
    front = []
    for s in range(S):
        z = FH + s * SH
        for i, (u0, u1) in enumerate(facade.evenly(W, bays, WIN_W)):
            uc = (u0 + u1) / 2
            if s == 0 and i == door_i:
                front.append(("door", uc - DOOR_W / 2, uc + DOOR_W / 2, z, z + DOOR_H))
            else:
                front.append(("window", u0, u1, z + SILL, z + SILL + WIN_H))
        door_uc = sum(facade.evenly(W, bays, WIN_W)[door_i]) / 2

    def windows(L, n):
        return [("window", u0, u1, FH + s * SH + SILL, FH + s * SH + SILL + WIN_H)
                for s in range(S) for (u0, u1) in (facade.evenly(L, n, WIN_W) if n else [])]

    ops = {"front": front, "back": windows(W, params["back_windows"]),
           "left": windows(D, params["side_windows"]), "right": windows(D, params["side_windows"])}
    for side in facade.SIDES:
        facade.wall_with_openings(k, tags, side, W, D, WALL_T, FH, zE, ops[side])
    for s in range(1, S):
        k.box("trim", (W + 0.3, D + 0.3, 0.25), (0, 0, FH + s * SH), bevel=0.0)
    k.box("walls", (W - 0.1, D - 0.1, 0.2), (0, 0, zE - 0.1), bevel=0.0)
    apex, _ = roofs.roof(k, {"roof": "roof", "wall": "walls"}, params["roof_form"], W, D, zE,
                         params["roof_pitch"], params["eave"])
    if params["chimney"]:
        top = apex + 1.5
        k.box("chimney", (1.3, 1.3, top - FH), (W * 0.28, 0, FH + (top - FH) / 2), bevel=0.0)
        k.box("chimney", (1.6, 1.6, 0.2), (W * 0.28, 0, top + 0.1), bevel=0.0)
    PD = params["porch_depth"]
    if params["porch"]:
        pw = min(W, 2.0 * W / bays)
        k.box("foundation", (pw, PD, FH + 0.15), (door_uc, -(D / 2 + PD / 2), (FH + 0.15) / 2), bevel=0.0)
        for sgn in (-1, 1):
            k.box("trim", (0.3, 0.3, SH - 0.7), (door_uc + sgn * (pw / 2 - 0.25), -(D / 2 + PD - 0.25),
                                                   FH + 0.15 + (SH - 0.7) / 2), bevel=0.0)
        k.box("roof", (pw + 0.6, PD + 0.6, 0.2), (door_uc, -(D / 2 + PD / 2 - 0.1), FH + SH - 0.45), bevel=0.0)
    s_ = max(W, D, apex)
    shots = [
        ("wide", (-W * 0.9, -(D * 1.6 + W * 0.9), apex * 0.8 + 2), (0.0, 0.0, apex * 0.45), 38.0),
        ("front", (door_uc - 3.0, -(D / 2 + PD + 7), FH + 5), (door_uc, -D / 2, FH + 4), 45.0),
    ]
    return BuildResult(k.parts, shots, {"W": W, "H": apex})
