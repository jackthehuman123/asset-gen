"""Art Deco tower: limestone piers with dark spandrels between window strips, setbacks with ledges,
a ground-floor portal and shopfronts, stepped crown with fins and a spire. Runs inside Blender."""
import random
from typing import Dict

from rbxasset.builders import arch
from rbxasset.builders.arch import Face, Op
from rbxasset.builders.kit import Kit
from rbxasset.builders.result import BuildResult

TAGS = ("base", "wall", "wall_b", "trim", "sash", "glass", "door", "soot", "iron", "groove", "roof",
        "ground", "curb", "road")
T0, GFH = 0.5, 14.0


def tier(k, W, D, z0, z1, fh, bays_f, bays_s, pw=1.1, out=0.8):
    """One tower tier: backing wall, glass strips, dark spandrels at each floor, projecting piers."""
    for side in ("front", "back", "left", "right"):
        F = Face(k, side, W, D)
        L = F.L
        n = bays_f if F.fb else bays_s
        bay = L / n
        zc = (z0 + z1) / 2
        F.box("wall", 0, zc, L, z1 - z0, 0.0, T0)
        for i in range(n):
            F.box("glass", -L / 2 + (i + 0.5) * bay, zc, bay - pw - 0.3, z1 - z0 - 0.2, 0.2, 0.06)
        nfl = int(round((z1 - z0) / fh))
        for f in range(nfl + 1):
            F.box("iron", 0, z0 + f * fh, L, 2.3, 0.45, 0.4)
        for i in range(nfl):
            F.box("sash", 0, z0 + (i + 0.5) * fh + 0.2, L, 0.12, 0.28, 0.1)
        for i in range(n + 1):
            u = -L / 2 + i * bay
            tag = "wall_b" if i in (0, n) else "wall"
            F.box(tag, u, zc + 0.5, pw + (0.9 if i in (0, n) else 0.0), z1 - z0 + 1.0, out, 1.0)
            F.box("trim", u, z1 + 1.4, pw * 0.7, 2.0, out - 0.2, 0.6)  # pier finial


def build(params: Dict, rng: random.Random) -> BuildResult:
    W, D, F, FH, S = (params[x] for x in ("width", "depth", "floors", "floor_height", "setbacks"))
    sb, bays = params["setback_depth"], params["bays"]
    k = Kit(TAGS)
    T = {r: r for r in TAGS}
    TB = dict(T, wall="base", wall_b="base")
    # ground floor: shopfronts and a central portal
    f0 = Face(k, "front", W, D)
    bay = W / bays
    ops = []
    for i in range(bays):
        u = -W / 2 + (i + 0.5) * bay
        if i == bays // 2:
            ops.append(Op("shop", u - 5.5, u + 5.5, 0.0, GFH - 2.5, bulkhead=0.0, door_u=u, panes=4))
        else:
            ops.append(Op("shop", u - bay / 2 + 1.3, u + bay / 2 - 1.3, 0.0, GFH - 3.5, bulkhead=1.4, panes=2))
    arch.wall(f0, TB, 0.0, GFH, ops, T0, rng, panel=6.0, vstep=GFH)
    for side in ("back", "left", "right"):
        Fa = Face(k, side, W, D)
        n = bays if Fa.fb else max(3, int(bays * D / W))
        ops_s = [Op("shop", -Fa.L / 2 + (i + 0.5) * Fa.L / n - 2.2, -Fa.L / 2 + (i + 0.5) * Fa.L / n + 2.2, 0.0,
                    GFH - 3.5, bulkhead=1.4, panes=2) for i in range(n)]
        arch.wall(Fa, TB, 0.0, GFH, ops_s, T0, rng, panel=6.0, vstep=GFH)
    for side in ("front", "back", "left", "right"):
        Fa = Face(k, side, W, D)
        Fa.box("trim", 0, GFH + 0.4, Fa.L + 1.2, 1.1, 0.7, 0.8)
        Fa.box("soot", 0, GFH - 0.9, Fa.L, 1.6, 0.03, 0.05)
    # portal surround: stepped nested frames and a metal canopy
    pu = 0.0
    for i, (w_, h_) in enumerate(((13.4, GFH - 0.5), (15.0, GFH + 0.4), (16.6, GFH + 1.4))):
        f0.box("trim", pu - w_ / 2 + 0.3, (h_) / 2, 0.6, h_, 0.5 + 0.18 * i, 0.5)
        f0.box("trim", pu + w_ / 2 - 0.3, (h_) / 2, 0.6, h_, 0.5 + 0.18 * i, 0.5)
    f0.box("iron", pu, 8.6, 14.0, 0.5, 3.2, 3.2)
    for sgn in (-1, 1):
        f0.box("iron", pu + sgn * 6.5, 8.0, 0.2, 1.4, 1.6, 0.2)

    # tower tiers with setbacks
    nt = S + 1
    base_fl = max(3, F // nt + (F - (F // nt) * nt))
    z = GFH
    fl_left = F
    w_, d_ = W, D
    for t in range(nt):
        fl = base_fl if t == 0 else max(2, (F - base_fl) // max(1, nt - 1))
        if t == nt - 1:
            fl = max(2, fl_left)
        fl = min(fl, fl_left)
        z1 = z + fl * FH
        tier(k, w_, d_, z, z1, FH, bays if t == 0 else max(4, bays - 2 * t), max(3, int(bays * d_ / w_)))
        for side in ("front", "back", "left", "right"):
            Fa = Face(k, side, w_, d_)
            Fa.box("trim", 0, z1 + 0.5, Fa.L + 1.6, 1.0, 1.0, 1.1)
            Fa.box("soot", 0, z1 - 1.0, Fa.L, 1.4, 0.03, 0.05)
        fl_left -= fl
        z = z1
        if t < nt - 1:
            k.box("roof", (w_ - 0.2, d_ - 0.2, 0.4), (0, 0, z + 0.2), bevel=0.0)
            w_, d_ = w_ - 2 * sb, d_ - 2 * sb
            z += 1.0
    k.box("roof", (w_ - 0.2, d_ - 0.2, 0.4), (0, 0, z + 0.2), bevel=0.0)
    top = z
    if params["crown"]:
        cw, cd = w_ * 0.62, d_ * 0.62
        for i, (sx, sy, hh) in enumerate(((0.8, 0.8, 5.0), (0.62, 0.62, 5.5), (0.42, 0.42, 6.0))):
            arch.frustum(k, "wall_b", (-w_ * sx / 2, w_ * sx / 2, -d_ * sy / 2, d_ * sy / 2, top),
                         (-w_ * sx / 2 * 0.86, w_ * sx / 2 * 0.86, -d_ * sy / 2 * 0.86, d_ * sy / 2 * 0.86, top + hh))
            top += hh
        for sx in (-1, 1):
            for sy in (-1, 1):
                k.box("trim", (1.4, 1.4, 11.0), (sx * w_ * 0.28, sy * d_ * 0.28, top - 12.0 + 5.5 + 6.0), bevel=0.0)
        k.cone("roof", 2.2, 0.15, 22.0, (0, 0, top + 11.0), verts=4, rot=(0, 0, 0.7853981))
        top += 22.0
    if params["street"]:
        arch.street_context(k, T, W + 8, D, front_depth=9.0, side=4.0)
    s = max(W, D)
    shots = [
        ("wide", (-top * 0.55, -(D / 2 + top * 1.45), top * 0.36), (0.0, 0.0, top * 0.42), 34.0),
        ("front", (-8, -(D / 2 + 26), 9), (0.0, -D / 2, 9), 42.0),
        ("crown", (-s * 0.9, -(D / 2 + s * 1.1), top * 0.88), (0.0, 0.0, top * 0.86), 40.0),
    ]
    return BuildResult(k.parts, shots, {"W": W, "H": top})
