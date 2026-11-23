"""Gothic revival church: buttressed stone nave with lancet windows, slate gable roof, west tower with a
pointed doorway, belfry openings, pinnacles and a spire. Runs inside Blender."""
import math
import random
from typing import Dict

from rbxasset.builders import arch, roofs
from rbxasset.builders.arch import Face, Op
from rbxasset.builders.kit import Kit
from rbxasset.builders.result import BuildResult

TAGS = ("base", "wall", "wall_b", "trim", "sash", "glass", "door", "soot", "iron", "roof", "ground", "curb", "road")
T0, BH = 0.8, 1.6


def build(params: Dict, rng: random.Random) -> BuildResult:
    W, D, WH = params["nave_width"], params["nave_length"], params["wall_height"]
    TW, TH, SH, bays = params["tower_width"], params["tower_height"], params["spire_height"], params["bays"]
    k = Kit(TAGS)
    T = {r: r for r in TAGS}
    zE = BH + WH
    k.box("base", (W + 0.5, D + 0.5, BH), (0, 0, BH / 2), bevel=0.0)
    # nave: lancet windows between buttresses
    for side in ("left", "right"):
        Fa = Face(k, side, W, D)
        ops = [Op("gothic", -D / 2 + (i + 0.5) * D / bays - 1.7, -D / 2 + (i + 0.5) * D / bays + 1.7, BH + 6.0,
                  BH + 6.0 + 3.4 * 0.866 + 8.0, style="plain") for i in range(bays)]
        arch.wall(Fa, T, BH, zE, ops, T0, rng, panel=5.0, vstep=8.0)
        for i in range(bays + 1):
            u = -D / 2 + i * D / bays
            Fa.box("wall_b", u, BH + WH * 0.4, 1.7, WH * 0.8, 1.6, 1.6)
            Fa.box("wall_b", u, BH + WH * 0.85, 1.4, WH * 0.3, 1.2, 1.2)
            Fa.box("trim", u, BH + WH * 1.0 - 0.1, 1.2, 0.5, 1.3, 1.3)
        Fa.box("soot", 0, zE - 1.4, D, 1.4, 0.03, 0.05)
    # rear wall with a large pointed window
    Fb = Face(k, "back", W, D)
    arch.wall(Fb, T, BH, zE, [Op("gothic", -3.4, 3.4, BH + 7.0, BH + 7.0 + 6.8 * 0.866 + 9.0)], T0, rng, panel=5.0)
    # tower on the front (west) end
    ty = -D / 2 - TW / 2 + 1.0
    zt = BH + TH
    k.box("base", (TW + 0.5, TW + 0.5, BH), (0, ty, BH / 2), bevel=0.0)
    ft = Face(k, "front", TW, TW, oy=ty + TW / 2)
    door = Op("gothic", -2.7, 2.7, BH, BH + 5.4 * 0.866 + 6.5, door=True)
    win_ = Op("gothic", -2.0, 2.0, BH + 19.0, BH + 19.0 + 4.0 * 0.866 + 7.0)
    arch.wall(ft, T, BH, zt, [door, win_], T0, rng, panel=5.0, vstep=10.0)
    for side in ("left", "right"):
        arch.wall(Face(k, side, TW, TW, oy=ty + TW / 2), T, BH, zt - 9.0,
                  [Op("gothic", -1.4, 1.4, BH + 13.0, BH + 13.0 + 2.8 * 0.866 + 6.0)], T0, rng, panel=5.0)
    # belfry stage with paired pointed louvers on all four faces
    for side in ("front", "back", "left", "right"):
        Fa = Face(k, side, TW, TW, oy=ty + TW / 2)
        arch.wall(Fa, T, zt - 9.0, zt, [Op("gothic", -2.2, -0.2, zt - 8.0, zt - 8.0 + 2.0 * 0.866 + 5.8),
                                        Op("gothic", 0.2, 2.2, zt - 8.0, zt - 8.0 + 2.0 * 0.866 + 5.8)], T0, rng, panel=5.0)
        for sgn in (-1, 1):
            Fa.box("wall_b", sgn * (Fa.L / 2), BH + TH * 0.45, 1.7, TH * 0.9, 1.5, 1.8)  # corner buttress
            Fa.box("wall_b", sgn * (Fa.L / 2), BH + TH * 0.88, 1.4, TH * 0.24, 1.3, 1.5)
        Fa.box("trim", 0, zt + 0.4, Fa.L + 1.2, 0.8, 0.9, 1.0)
        Fa.box("soot", 0, zt - 9.5, Fa.L, 1.2, 0.03, 0.05)
    k.box("roof", (TW + 0.6, TW + 0.6, 0.5), (0, ty, zt + 0.25), bevel=0.0)
    # spire and pinnacles
    k.cone("roof", TW * 0.78, 0.18, SH, (0, ty, zt + SH / 2), verts=4, rot=(0, 0, math.pi / 4))
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = sx * (TW / 2 - 0.6), ty + sy * (TW / 2 - 0.6)
            k.box("wall_b", (1.1, 1.1, 3.0), (px, py, zt + 1.5), bevel=0.0)
            k.cone("roof", 0.9, 0.08, 2.6, (px, py, zt + 4.3), verts=4, rot=(0, 0, math.pi / 4))
    k.box("iron", (0.16, 0.16, 3.0), (0, ty, zt + SH + 1.4), bevel=0.0)
    k.box("iron", (1.4, 0.16, 0.16), (0, ty, zt + SH + 2.2), bevel=0.0)
    # nave roof
    apex, objs = roofs.roof(k, {"roof": "roof", "wall": "wall"}, "gable", D, W, zE, 56.0, 1.0)
    roofs.placed(objs, 0.0, 0.0, math.pi / 2)  # the ridge runs along the nave (y)
    if params["street"]:
        arch.street_context(k, T, W + 14, D + TW, front_depth=9.0, side=5.0)
    top = zt + SH + 3.5
    shots = [
        ("wide", (-W * 2.4, -(D / 2 + TW + 70), top * 0.45), (0.0, -D * 0.15, top * 0.38), 36.0),
        ("front", (-5, -(D / 2 + TW + 24), BH + 12), (0.0, ty - TW / 2, BH + 12), 42.0),
        ("spire", (-12, -(D / 2 + TW + 20), zt + 6), (0.0, ty, zt + 6), 45.0),
    ]
    return BuildResult(k.parts, shots, {"W": W, "H": top})
