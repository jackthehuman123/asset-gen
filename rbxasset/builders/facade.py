"""Walls with openings, built from boxes. Runs inside Blender. Units: studs.

A wall plane is the outer face of the building footprint (W wide in x, D deep in y).
`u` runs along x for front/back and along y for left/right; `v` is world z.
Openings are (kind, u0, u1, v0, v1) with kind in window, door, big_door.
tags: {"wall", "trim", "glazing", "door"} -> part tag names."""

import math

SIDES = ("front", "back", "left", "right")


def place(side, W, D, u, z, su, sz, out, th):
    """Box centre and size for a slab whose outer face sits `out` beyond the wall plane."""
    if side == "front":
        return (u, -(D / 2 + out - th / 2), z), (su, th, sz)
    if side == "back":
        return (u, D / 2 + out - th / 2, z), (su, th, sz)
    if side == "left":
        return (-(W / 2 + out - th / 2), u, z), (th, su, sz)
    return (W / 2 + out - th / 2, u, z), (th, su, sz)


def _b(kit, tag, side, W, D, u, z, su, sz, out, th, rot=(0, 0, 0)):
    loc, size = place(side, W, D, u, z, su, sz, out, th)
    return kit.box(tag, size, loc, rot=rot, bevel=0.0)


def fit_opening(kit, tags, side, W, D, t, op):
    """Frame, glazing or door leaf for one opening in a wall of thickness t."""
    kind, u0, u1, v0, v1 = op
    w, h, uc, vc = u1 - u0, v1 - v0, (u0 + u1) / 2, (v0 + v1) / 2
    tr, gl, dr = tags["trim"], tags["glazing"], tags["door"]
    if kind == "window":
        j = 0.16
        for u in (u0 + j / 2, u1 - j / 2):
            _b(kit, tr, side, W, D, u, vc, j, h, 0.1, 0.22)
        _b(kit, tr, side, W, D, uc, v1 + 0.125, w + 0.4, 0.25, 0.14, 0.28)
        _b(kit, tr, side, W, D, uc, v0 - 0.09, w + 0.3, 0.18, 0.2, 0.3)
        _b(kit, tr, side, W, D, uc, vc, 0.07, h - 0.1, -(t / 2 - 0.05), 0.06)
        _b(kit, tr, side, W, D, uc, vc, w - 0.3, 0.07, -(t / 2 - 0.05), 0.06)
        _b(kit, gl, side, W, D, uc, vc, w, h, -(t / 2 - 0.02), 0.04)
    elif kind == "door":
        j = 0.22
        _b(kit, dr, side, W, D, uc, v0 + (h - 0.15) / 2, w - 0.2, h - 0.15, -0.02, 0.14)
        for u in (u0 + j / 2, u1 - j / 2):
            _b(kit, tr, side, W, D, u, vc, j, h, 0.12, 0.3)
        _b(kit, tr, side, W, D, uc, v1 + 0.15, w + 0.5, 0.3, 0.14, 0.3)
        _b(kit, dr, side, W, D, u1 - 0.55, v0 + h * 0.45, 0.14, 0.14, 0.1, 0.14)
    elif kind == "big_door":
        assert side in ("front", "back"), "big_door only on front/back"
        lw = w / 2 - 0.05
        for sgn in (-1, 1):
            cx = uc + sgn * (lw / 2 + 0.05)
            _b(kit, dr, side, W, D, cx, vc, lw, h, -0.02, 0.18)
            ang = math.atan2(h, lw)
            for a in (ang, -ang):
                _b(
                    kit,
                    tr,
                    side,
                    W,
                    D,
                    cx,
                    vc,
                    math.hypot(lw, h) * 0.92,
                    0.22,
                    0.08,
                    0.1,
                    rot=(0, a, 0),
                )
        for u in (u0 - 0.1, u1 + 0.1):
            _b(kit, tr, side, W, D, u, vc, 0.2, h + 0.2, 0.14, 0.3)
        _b(kit, tr, side, W, D, uc, v1 + 0.2, w + 0.6, 0.3, 0.16, 0.3)
    else:
        raise ValueError("unknown opening kind %r" % kind)


def wall_with_openings(kit, tags, side, W, D, t, z0, z1, openings):
    """Solid wall pieces around the openings, plus the opening details."""
    L = W if side in ("front", "back") else D
    vs = sorted({z0, z1} | {o[3] for o in openings} | {o[4] for o in openings})
    vs = [v for v in vs if z0 <= v <= z1]
    for va, vb in zip(vs, vs[1:]):
        if vb - va < 1e-6:
            continue
        cover = sorted(
            (o[1], o[2]) for o in openings if o[3] <= va + 1e-6 and o[4] >= vb - 1e-6
        )
        cur = -L / 2
        for a, b in cover + [(L / 2, L / 2)]:
            if a - cur > 1e-6:
                _b(
                    kit,
                    tags["wall"],
                    side,
                    W,
                    D,
                    (cur + a) / 2,
                    (va + vb) / 2,
                    a - cur,
                    vb - va,
                    0.0,
                    t,
                )
            cur = max(cur, b)
    for op in openings:
        fit_opening(kit, tags, side, W, D, t, op)


def evenly(L, n, w):
    """n openings of width w centred in n equal bays across length L: list of (u0, u1)."""
    return [
        (-L / 2 + (i + 0.5) * L / n - w / 2, -L / 2 + (i + 0.5) * L / n + w / 2)
        for i in range(n)
    ]
