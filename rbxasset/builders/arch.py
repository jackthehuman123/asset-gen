"""Architectural detail library for realistic buildings. Runs inside Blender. Units: studs.

A `Face` is one wall plane of a W x D footprint (optionally shifted by ox, oy): `u` runs along the
wall (x for front/back, y for left/right), `z` is height, `out` is distance beyond the plane.
Everything is built from boxes and extruded polygons through a shared `Kit`.

Part tags are passed as a dict `T` (role -> part tag). Roles used here:
wall, wall_b (colour variant), trim, sash, glass, door, soot, iron, groove, shutter, awning, roof,
ground, curb. Missing roles fall back to `trim` (or `wall`)."""

import math

from rbxasset.builders.kit import Kit


class Face:
    def __init__(self, kit, side, W, D, ox=0.0, oy=0.0):
        self.kit, self.side, self.W, self.D, self.ox, self.oy = kit, side, W, D, ox, oy
        self.fb = side in ("front", "back")
        self.L = W if self.fb else D

    def pt(self, u, z, out):
        s, W, D = self.side, self.W, self.D
        if s == "front":
            return (u + self.ox, -(D / 2 + out) + self.oy, z)
        if s == "back":
            return (u + self.ox, D / 2 + out + self.oy, z)
        if s == "left":
            return (-(W / 2 + out) + self.ox, u + self.oy, z)
        return (W / 2 + out + self.ox, u + self.oy, z)

    def box(self, tag, u, z, su, sz, out, th, rot=(0, 0, 0)):
        """Slab whose outer face is `out` beyond the plane, th thick (extends inward)."""
        loc = self.pt(u, z, out - th / 2)
        size = (su, th, sz) if self.fb else (th, su, sz)
        return self.kit.box(tag, size, loc, rot=rot, bevel=0.0)

    def rbox(self, tag, u, z, length, height, out, th, angle):
        """Box in the wall plane, rotated by `angle` (radians, rising with u)."""
        rot = (0, -angle, 0) if self.fb else (angle, 0, 0)
        return self.box(tag, u, z, length, height, out, th, rot=rot)

    def poly(self, tag, pts, out0, out1):
        """Extrude a (u, z) polygon between two out distances."""
        n = len(pts)
        verts = [self.pt(u, z, out0) for u, z in pts] + [
            self.pt(u, z, out1) for u, z in pts
        ]
        faces = [list(range(n)), list(range(2 * n - 1, n - 1, -1))]
        faces += [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
        return self.kit.mesh(tag, verts, faces)


class Op:
    """An opening in a wall: kind window|arch|door|shop|bigdoor, bounds in (u, z), options."""

    def __init__(self, kind, u0, u1, v0, v1, **opts):
        self.kind, self.u0, self.u1, self.v0, self.v1, self.opts = (
            kind,
            u0,
            u1,
            v0,
            v1,
            opts,
        )

    @property
    def uc(self):
        return (self.u0 + self.u1) / 2

    @property
    def w(self):
        return self.u1 - self.u0

    @property
    def h(self):
        return self.v1 - self.v0


def win(uc, z0, w, h, kind="window", **opts):
    return Op(kind, uc - w / 2, uc + w / 2, z0, z0 + h, **opts)


def tg(T, role):
    return T.get(role) or T.get("trim") or T["wall"]


def _arc(cx, cz, r, t0, t1, n):
    return [
        (
            cx + r * math.cos(t0 + (t1 - t0) * i / n),
            cz + r * math.sin(t0 + (t1 - t0) * i / n),
        )
        for i in range(n + 1)
    ]


# ------------------------------------------------------------------ walls
def wall(F, T, z0, z1, ops, t, rng=None, panel=6.0, vstep=9.0, variant=0.2):
    """Solid wall pieces around openings (split into panels so colour variants read), plus details."""
    L = F.L
    vs = {z0, z1} | {o.v0 for o in ops} | {o.v1 for o in ops}
    k = 1
    while z0 + k * vstep < z1 - 1.0:
        vs.add(z0 + k * vstep)
        k += 1
    vs = sorted(v for v in vs if z0 <= v <= z1)
    for va, vb in zip(vs, vs[1:]):
        if vb - va < 1e-6:
            continue
        cover = sorted(
            (o.u0, o.u1) for o in ops if o.v0 <= va + 1e-6 and o.v1 >= vb - 1e-6
        )
        cur = -L / 2
        for a, b in cover + [(L / 2, L / 2)]:
            if a - cur > 1e-6:
                n = max(1, int(math.ceil((a - cur) / panel)))
                for i in range(n):
                    ua, ub = cur + (a - cur) * i / n, cur + (a - cur) * (i + 1) / n
                    tag = (
                        T["wall_b"]
                        if (rng and T.get("wall_b") and rng.random() < variant)
                        else T["wall"]
                    )
                    F.box(tag, (ua + ub) / 2, (va + vb) / 2, ub - ua, vb - va, 0.0, t)
            cur = max(cur, b)
    for op in ops:
        opening(F, T, t, op)


# ------------------------------------------------------------------ openings
def opening(F, T, t, op):
    {
        "window": _window,
        "arch": _window,
        "gothic": _window,
        "door": _door,
        "shop": _shop,
        "bigdoor": _bigdoor,
    }[op.kind](F, T, t, op)


def _sash(F, T, op, out, rows, cols, arch_spring=None):
    uc, w, h = op.uc, op.w, op.h
    j = 0.1
    s = tg(T, "sash")
    for u in (op.u0 + j / 2, op.u1 - j / 2):
        F.box(s, u, op.v0 + h / 2, j, h, out, 0.1)
    F.box(s, uc, op.v0 + j / 2, w, j, out, 0.1)
    if arch_spring is None:
        F.box(s, uc, op.v1 - j / 2, w, j, out, 0.1)
    top = op.v1 if arch_spring is None else arch_spring
    for c in range(1, cols):
        F.box(
            s,
            op.u0 + w * c / cols,
            (op.v0 + top) / 2,
            0.06,
            top - op.v0,
            out + 0.01,
            0.07,
        )
    for r in range(1, rows):
        F.box(s, uc, op.v0 + (top - op.v0) * r / rows, w, 0.06, out + 0.01, 0.07)


def _arch_pts(op, gothic, n=10):
    """(spring z, points right spring -> apex -> left spring); apex is index n//2."""
    w, uc = op.w, op.uc
    if not gothic:
        spring = op.v1 - w / 2
        return spring, _arc(uc, spring, w / 2, 0, math.pi, n)
    spring = op.v1 - w * math.sqrt(3) / 2
    right = _arc(op.u0, spring, w, 0, math.pi / 3, n // 2)
    left = _arc(op.u1, spring, w, 2 * math.pi / 3, math.pi, n // 2)
    return spring, right + left[1:]


def _ring(F, tag, pts, offset, width, out, th):
    """A band of boxes following an arch polyline, offset outward by `offset`."""
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        dx, dz = x1 - x0, z1 - z0
        ln = math.hypot(dx, dz)
        nx, nz = dz / ln, -dx / ln
        F.rbox(
            tag,
            (x0 + x1) / 2 + nx * offset,
            (z0 + z1) / 2 + nz * offset,
            ln + 0.08,
            width,
            out,
            th,
            math.atan2(dz, dx),
        )


def _window(F, T, t, op):
    o, arch, gothic = op.opts, op.kind in ("arch", "gothic"), op.kind == "gothic"
    uc, w, h, v0, v1 = op.uc, op.w, op.h, op.v0, op.v1
    glass_out = -(t * 0.5)
    spring, pts = _arch_pts(op, gothic) if arch else (None, None)
    if arch:
        F.poly(T["wall"], [(op.u0, spring), (op.u0, v1), (uc, v1)] + pts[6:10], 0.0, -t)
        F.poly(
            T["wall"],
            [(op.u1, spring), (op.u1, v1), (uc, v1)] + [pts[4], pts[3], pts[2], pts[1]],
            0.0,
            -t,
        )
        F.poly(
            T["door"] if o.get("door") else T["glass"],
            [(op.u0, v0), (op.u1, v0)] + pts,
            glass_out,
            glass_out - 0.05,
        )
        s_ = tg(T, "sash")
        for u in (op.u0 + 0.05, op.u1 - 0.05):
            F.box(s_, u, (v0 + spring) / 2, 0.1, spring - v0, glass_out + 0.06, 0.1)
        F.box(s_, uc, v0 + 0.05, w, 0.1, glass_out + 0.06, 0.1)
        F.box(s_, uc, spring, w, 0.08, glass_out + 0.07, 0.1)
        F.box(s_, uc, (v0 + v1) / 2 - 0.2, 0.07, v1 - v0 - 0.4, glass_out + 0.07, 0.08)
        _ring(F, s_, pts, 0.0, 0.1, glass_out + 0.06, 0.1)
    else:
        F.box(T["glass"], uc, (v0 + v1) / 2, w, h, glass_out, 0.05)
        _sash(
            F,
            T,
            op,
            glass_out + 0.06,
            o.get("rows", 2),
            o.get("cols", 2 if w > 2.0 else 1),
        )
    style = o.get("style", "plain")
    tr = tg(T, "trim")
    # sill, soot below it, then the head treatment
    if v0 > 0.3:
        F.box(tr, uc, v0 - 0.12, w + 0.55, 0.24, 0.4, 0.5)
    if o.get("soot", True) and T.get("soot") and v0 > 0.8:
        lo, hi = max(0.0, v0 - 1.55), v0 - 0.35
        if hi - lo > 0.3:
            F.box(T["soot"], uc, (lo + hi) / 2, w + 0.15, hi - lo, 0.03, 0.05)
    j = 0.3 if style in ("surround", "hooded", "pediment", "arch") else 0.15
    if not arch:
        for u in (op.u0 - j / 2 + 0.02, op.u1 + j / 2 - 0.02):
            F.box(tr, u, (v0 + v1) / 2, j, h + 0.1, 0.16, 0.28)
    if style == "plain" and not arch:
        F.box(tr, uc, v1 + 0.15, w + 0.5, 0.3, 0.18, 0.3)
    elif style == "hooded" and not arch:
        F.box(tr, uc, v1 + 0.15, w + 0.6, 0.3, 0.2, 0.32)
        F.box(tr, uc, v1 + 0.45, w + 1.0, 0.22, 0.6, 0.6)
        F.box(tr, uc, v1 + 0.65, w + 1.1, 0.16, 0.66, 0.66)
        for u in (op.u0 - 0.15, op.u1 + 0.15):
            F.box(tr, u, v1 - 0.25, 0.28, 0.8, 0.5, 0.5)
        F.box(tr, uc, v1 + 0.2, 0.45, 0.55, 0.3, 0.3)
    elif style == "pediment" and not arch:
        F.box(tr, uc, v1 + 0.15, w + 0.7, 0.3, 0.2, 0.32)
        ph = (w + 0.9) * 0.22
        F.poly(
            tr,
            [
                (uc - (w + 0.9) / 2, v1 + 0.3),
                (uc + (w + 0.9) / 2, v1 + 0.3),
                (uc, v1 + 0.3 + ph),
            ],
            0.55,
            0.0,
        )
    elif arch:
        _ring(F, tr, pts, 0.2, 0.38, 0.22, 0.3)
        F.box(tr, uc, v1 + 0.25, 0.55, 0.9, 0.35, 0.42)  # keystone
        for u in (op.u0 - 0.18, op.u1 + 0.18):
            F.box(tr, u, (v0 + spring) / 2 + 0.05, 0.34, spring - v0 + 0.1, 0.2, 0.3)
            F.box(tr, u, spring, 0.45, 0.18, 0.3, 0.4)  # impost
    if o.get("shutters"):
        sw = min(1.1, w / 2 * 0.95)
        for sgn in (-1, 1):
            u = uc + sgn * (w / 2 + sw / 2 + 0.2)
            F.box(T.get("shutter") or tr, u, (v0 + v1) / 2, sw, h, 0.12, 0.12)
            for k in range(1, 7):
                F.box(
                    T.get("shutter") or tr, u, v0 + h * k / 7, sw - 0.1, 0.05, 0.17, 0.1
                )
    if o.get("ac") and T.get("iron"):
        F.box(T["iron"], uc, v0 + 0.35, w * 0.7, 0.7, 0.9, 0.7)


def _door(F, T, t, op):
    o = op.opts
    uc, w, h, v0, v1 = op.uc, op.w, op.h, op.v0, op.v1
    tr = tg(T, "trim")
    transom = o.get("transom", 0.0)
    dh = h - transom
    F.box(T["door"], uc, v0 + dh / 2, w - 0.2, dh, -0.05, 0.14)
    for cx in (-0.22, 0.22):
        for cz, ch in ((0.3, 0.45), (0.75, 0.36)):
            F.box(
                T["door"], uc + cx * w, v0 + dh * cz, w * 0.34, dh * ch * 0.8, 0.0, 0.12
            )
    if transom:
        F.box(T["glass"], uc, v0 + dh + transom / 2, w - 0.2, transom - 0.1, -0.2, 0.05)
        F.box(tg(T, "sash"), uc, v0 + dh + 0.03, w, 0.08, -0.12, 0.1)
        for c in range(1, 4):
            F.box(
                tg(T, "sash"),
                op.u0 + w * c / 4,
                v0 + dh + transom / 2,
                0.05,
                transom - 0.1,
                -0.1,
                0.08,
            )
    for u in (op.u0 + 0.14, op.u1 - 0.14):
        F.box(tr, u, (v0 + v1) / 2 + 0.025, 0.28, h + 0.05, 0.22, 0.34)
    F.box(tr, uc, v1 + 0.15, w + 0.7, 0.32, 0.26, 0.36)
    if o.get("hood", True):
        F.box(tr, uc, v1 + 0.45, w + 1.1, 0.22, 0.7, 0.7)
    if T.get("iron"):
        F.box(T["iron"], op.u1 - 0.55, v0 + dh * 0.45, 0.16, 0.16, 0.12, 0.14)


def _shop(F, T, t, op):
    o = op.opts
    tr, s = tg(T, "trim"), tg(T, "sash")
    bulk = o.get("bulkhead", 1.1)
    F.box(tr, op.uc, op.v0 + bulk / 2, op.w, bulk, -0.1, 0.25)
    gz0, gz1 = op.v0 + bulk, op.v1
    F.box(T["glass"], op.uc, (gz0 + gz1) / 2, op.w, gz1 - gz0, -(t * 0.5), 0.05)
    n = o.get("panes", max(2, int(op.w // 3.5)))
    for c in range(n + 1):
        F.box(
            s,
            op.u0 + op.w * c / n,
            (gz0 + gz1) / 2,
            0.14,
            gz1 - gz0,
            -(t * 0.5) + 0.07,
            0.12,
        )
    F.box(s, op.uc, gz1 - 0.1, op.w, 0.2, -(t * 0.5) + 0.07, 0.12)
    F.box(s, op.uc, gz0 + 0.07, op.w, 0.14, -(t * 0.5) + 0.07, 0.12)
    tz = gz1 - 1.1
    F.box(s, op.uc, tz, op.w, 0.1, -(t * 0.5) + 0.07, 0.12)  # transom bar
    if o.get("door_u") is not None:
        du, dw = o["door_u"], 3.0
        F.box(T["door"], du, gz0 + (tz - gz0) / 2, dw, tz - gz0, -(t * 0.5) + 0.1, 0.1)
        F.box(
            T["glass"],
            du,
            gz0 + (tz - gz0) / 2 + 0.2,
            dw - 0.7,
            tz - gz0 - 1.0,
            -(t * 0.5) + 0.16,
            0.04,
        )
    for u in (op.u0 - 0.25, op.u1 + 0.25):
        F.box(tr, u, (op.v0 + op.v1) / 2 + 0.1, 0.5, op.h + 0.2, 0.24, 0.4)


def _bigdoor(F, T, t, op):
    lw = op.w / 2 - 0.05
    for sgn in (-1, 1):
        cx = op.uc + sgn * (lw / 2 + 0.05)
        F.box(T["door"], cx, (op.v0 + op.v1) / 2, lw, op.h, -0.02, 0.18)
        ang = math.atan2(op.h, lw)
        for a in (ang, -ang):
            F.rbox(
                tg(T, "trim"),
                cx,
                (op.v0 + op.v1) / 2,
                math.hypot(lw, op.h) * 0.92,
                0.22,
                0.08,
                0.1,
                a,
            )
    for u in (op.u0 - 0.1, op.u1 + 0.1):
        F.box(tg(T, "trim"), u, (op.v0 + op.v1) / 2, 0.2, op.h + 0.2, 0.14, 0.3)
    F.box(tg(T, "trim"), op.uc, op.v1 + 0.2, op.w + 0.6, 0.3, 0.16, 0.3)


# ------------------------------------------------------------------ ornament
def cornice(
    kit,
    T,
    W,
    D,
    z,
    proj=1.5,
    h=1.6,
    brackets=True,
    dentils=False,
    step=1.0,
    ox=0.0,
    oy=0.0,
    sides=("front", "back", "left", "right"),
    tag=None,
):
    """Stepped cornice ring with optional brackets and dentils; z is the top of the crown."""
    tr = tag or tg(T, "trim")
    for side in sides:
        F = Face(kit, side, W, D, ox, oy)
        L = F.L + 2 * proj
        F.box(tr, 0, z - 0.14, L, 0.28, proj + 0.1, 0.3)  # crown
        F.box(tr, 0, z - 0.5, L, 0.42, proj, 0.5)  # corona
        F.box(tr, 0, z - h + 0.15, F.L + 0.5, 0.3, 0.25, 0.3)  # architrave
        F.box(tr, 0, z - h / 2 - 0.2, F.L + 0.2, h - 1.15, 0.12, 0.14)  # frieze
        if dentils:
            n = int(F.L / 0.5)
            for i in range(n):
                F.box(
                    tr, -F.L / 2 + (i + 0.5) * F.L / n, z - 0.85, 0.22, 0.22, 0.55, 0.3
                )
        if brackets:
            n = max(1, int(F.L / step))
            for i in range(n + 1):
                F.box(
                    tr,
                    -F.L / 2 + i * F.L / n,
                    z - 1.0,
                    0.34,
                    0.7,
                    proj * 0.85,
                    proj * 0.85 - 0.05,
                )


def course(
    kit,
    tag,
    W,
    D,
    z,
    proj=0.3,
    h=0.4,
    ox=0.0,
    oy=0.0,
    sides=("front", "back", "left", "right"),
):
    """A projecting belt course around the building."""
    for side in sides:
        F = Face(kit, side, W, D, ox, oy)
        F.box(tag, 0, z, F.L + 2 * proj, h, proj, proj + 0.05)


def quoins(kit, tag, W, D, z0, z1, size=1.5, h=0.75, ox=0.0, oy=0.0):
    n = int((z1 - z0) / h)
    for side in ("front", "back", "left", "right"):
        F = Face(kit, side, W, D, ox, oy)
        for i in range(n):
            long_ = size if (i + (side in ("left", "right"))) % 2 == 0 else size * 0.55
            for sgn in (-1, 1):
                F.box(
                    tag,
                    sgn * (F.L / 2 - long_ / 2),
                    z0 + (i + 0.5) * h,
                    long_,
                    h - 0.06,
                    0.12,
                    0.2,
                )


def rustication(kit, tag, W, D, z0, z1, h=1.2, ox=0.0, oy=0.0):
    """Horizontal joint lines (dark thin boxes) on all four faces."""
    n = int((z1 - z0) / h)
    for side in ("front", "back", "left", "right"):
        F = Face(kit, side, W, D, ox, oy)
        for i in range(1, n):
            F.box(tag, 0, z0 + i * h, F.L, 0.07, 0.025, 0.05)


def balcony(F, T, uc, z, w, depth=1.8, rail_h=3.2, post_step=0.55):
    tr, ir = tg(T, "trim"), tg(T, "iron")
    F.box(tr, uc, z, w, 0.3, depth, depth)
    for u in (uc - w / 2 + 0.4, uc + w / 2 - 0.4):
        F.box(tr, u, z - 0.55, 0.3, 0.8, depth - 0.3, depth - 0.3)
    n = max(2, int(w / post_step))
    for i in range(n + 1):
        u = uc - w / 2 + 0.1 + (w - 0.2) * i / n
        F.box(ir, u, z + 0.15 + rail_h / 2, 0.07, rail_h, depth - 0.1, 0.07)
    for dz in (0.2, rail_h):
        F.box(ir, uc, z + 0.15 + dz, w, 0.1, depth - 0.05, 0.12)
    for sgn in (-1, 1):
        F.box(
            ir,
            uc + sgn * (w / 2 - 0.05),
            z + 0.15 + rail_h / 2,
            0.07,
            rail_h,
            depth / 2,
            depth - 0.1,
        )


def oriel(F, T, uc, z0, w, h, depth=1.8, roof=True):
    """Projecting bay: corbel, glazed front and cheeks, cap."""
    tr = tg(T, "trim")
    F.box(tr, uc, z0 - 0.4, w + 0.3, 0.8, depth + 0.1, depth + 0.1)
    for sgn in (-1, 1):
        F.box(
            tg(T, "wall"), uc + sgn * (w / 2 - 0.15), z0 + h / 2, 0.3, h, depth, depth
        )
    F.box(tg(T, "wall"), uc, z0 + 0.35, w, 0.7, depth, 0.3)
    F.box(tg(T, "wall"), uc, z0 + h - 0.35, w, 0.7, depth, 0.3)
    F.box(T["glass"], uc, z0 + h / 2, w - 0.6, h - 1.4, depth - 0.1, 0.05)
    for c in range(1, 3):
        F.box(
            tg(T, "sash"),
            uc - (w - 0.6) / 2 + (w - 0.6) * c / 3,
            z0 + h / 2,
            0.07,
            h - 1.4,
            depth - 0.05,
            0.09,
        )
    F.box(tg(T, "sash"), uc, z0 + h / 2, w - 0.6, 0.07, depth - 0.05, 0.09)
    for sgn in (-1, 1):
        F.box(
            T["glass"],
            uc + sgn * (w / 2 - 0.05),
            z0 + h / 2,
            0.05,
            h - 1.4,
            depth - 0.5,
            depth - 0.7,
        )
    if roof:
        F.box(tr, uc, z0 + h + 0.15, w + 0.5, 0.3, depth + 0.35, depth + 0.4)


def column(kit, tag, x, y, z0, z1, r=0.38, capital=True):
    kit.box(tag, (r * 2.6, r * 2.6, 0.35), (x, y, z0 + 0.175), bevel=0.0)
    kit.cyl(
        tag,
        r,
        z1 - z0 - 0.35 - (0.5 if capital else 0),
        (x, y, z0 + 0.35 + (z1 - z0 - 0.35 - (0.5 if capital else 0)) / 2),
        verts=14,
    )
    if capital:
        kit.box(tag, (r * 2.8, r * 2.8, 0.5), (x, y, z1 - 0.25), bevel=0.0)


def portico(F, T, uc, z0, w, depth, h, columns=4, pediment=True, steps=3):
    """Pedimented porch: columns, entablature, optional pediment, stair."""
    tr = tg(T, "trim")
    F.box(tr, uc, z0 + 0.15, w, 0.3, depth, depth)
    for i in range(columns):
        u = uc - w / 2 + 0.7 + (w - 1.4) * i / (columns - 1)
        p = F.pt(u, z0 + 0.3, depth - 0.7)
        column(F.kit, tr, p[0], p[1], z0 + 0.3, z0 + h)
    F.box(tr, uc, z0 + h + 0.3, w + 0.4, 0.6, depth + 0.2, depth + 0.2)
    F.box(tr, uc, z0 + h + 0.7, w + 0.7, 0.2, depth + 0.35, depth + 0.35)
    if pediment:
        F.poly(
            tr,
            [
                (uc - w / 2 - 0.2, z0 + h + 0.8),
                (uc + w / 2 + 0.2, z0 + h + 0.8),
                (uc, z0 + h + 0.8 + w * 0.17),
            ],
            depth + 0.35,
            0.0,
        )
    for i in range(steps):
        F.box(
            tr,
            uc,
            z0 - 0.3 * (i + 0.5) + 0.0,
            w * 0.6 + 0.6 * i,
            0.3,
            depth + 0.6 * (i + 1),
            0.6,
        )


def awning(F, T, u0, u1, z, depth=2.6, drop=1.4):
    a = math.atan2(drop, depth)
    uc, w = (u0 + u1) / 2, u1 - u0
    length = math.hypot(depth, drop)
    loc = F.pt(uc, z - drop / 2, depth / 2)
    ap = T.get("awning") or tg(T, "trim")
    if F.fb:
        F.kit.box(
            ap,
            (w, length, 0.08),
            loc,
            rot=(a if F.side == "front" else -a, 0, 0),
            bevel=0.0,
        )
    else:
        F.kit.box(
            ap,
            (length, w, 0.08),
            loc,
            rot=(0, a if F.side == "right" else -a, 0),
            bevel=0.0,
        )
    F.box(ap, uc, z - drop - 0.2, w, 0.45, depth, 0.06)  # valance
    for u in (u0, u1):
        F.box(tg(T, "iron"), u, z - drop / 2, 0.06, drop, depth, 0.06)


def chimney(kit, tag, x, y, z0, z1, w=1.5, d=1.5, pots=2):
    kit.box(tag, (w, d, z1 - z0), (x, y, z0 + (z1 - z0) / 2), bevel=0.0)
    kit.box(tag, (w + 0.4, d + 0.4, 0.3), (x, y, z1 + 0.15), bevel=0.0)
    for i in range(pots):
        kit.cyl(
            tag, 0.28, 0.9, (x + (i - (pots - 1) / 2) * 0.6, y, z1 + 0.75), verts=10
        )


def balustrade(kit, tag, W, D, z, h=1.3, step=0.55, ox=0.0, oy=0.0):
    for side in ("front", "back", "left", "right"):
        F = Face(kit, side, W, D, ox, oy)
        n = max(2, int(F.L / step))
        for i in range(n + 1):
            F.box(tag, -F.L / 2 + F.L * i / n, z + h / 2, 0.2, h, 0.15, 0.2)
        F.box(tag, 0, z + h + 0.1, F.L + 0.4, 0.2, 0.25, 0.4)
        F.box(tag, 0, z + 0.1, F.L + 0.3, 0.2, 0.2, 0.3)


def turret(kit, T, x, y, z0, r, h, roof_h, windows=True):
    tr = tg(T, "trim")
    kit.cyl(T["wall"], r, h, (x, y, z0 + h / 2), verts=16)
    kit.cyl(tr, r + 0.25, 0.4, (x, y, z0 + 0.2), verts=16)
    kit.cyl(tr, r + 0.3, 0.35, (x, y, z0 + h - 0.2), verts=16)
    if windows:
        for k in range(8):
            a = math.pi * 2 * k / 8
            if k % 2 == 0:
                continue
            kit.box(
                T["glass"],
                (0.9, 0.06, 2.0),
                (
                    x + (r + 0.02) * math.cos(a),
                    y + (r + 0.02) * math.sin(a),
                    z0 + h * 0.55,
                ),
                rot=(0, 0, a + math.pi / 2),
                bevel=0.0,
            )
            kit.box(
                tg(T, "sash"),
                (1.1, 0.1, 2.2),
                (
                    x + (r + 0.0) * math.cos(a),
                    y + (r + 0.0) * math.sin(a),
                    z0 + h * 0.55,
                ),
                rot=(0, 0, a + math.pi / 2),
                bevel=0.0,
            )
    kit.cone(T["roof"], r + 0.9, 0.12, roof_h, (x, y, z0 + h + roof_h / 2), verts=16)
    kit.cyl(tr, 0.07, 1.2, (x, y, z0 + h + roof_h + 0.5), verts=6)


def frustum(kit, tag, bottom, top):
    """Closed solid between two rectangles: bottom/top = (x0, x1, y0, y1, z)."""
    bx0, bx1, by0, by1, bz = bottom
    tx0, tx1, ty0, ty1, tz = top
    v = [
        (bx0, by0, bz),
        (bx1, by0, bz),
        (bx1, by1, bz),
        (bx0, by1, bz),
        (tx0, ty0, tz),
        (tx1, ty0, tz),
        (tx1, ty1, tz),
        (tx0, ty1, tz),
    ]
    f = [
        [3, 2, 1, 0],
        [4, 5, 6, 7],
        [0, 1, 5, 4],
        [1, 2, 6, 5],
        [2, 3, 7, 6],
        [3, 0, 4, 7],
    ]
    return kit.mesh(tag, v, f)


def fire_escape(F, T, uc, z0, floors, floor_h, w=4.0, depth=1.6):
    """Landings with railings at each floor, a drop ladder strip alongside."""
    ir = tg(T, "iron")
    for i in range(floors):
        z = z0 + i * floor_h
        F.box(ir, uc, z, w, 0.12, depth, depth)
        for dz in (0.1, 3.0):
            F.box(ir, uc, z + dz, w, 0.08, depth, 0.08)
        for sgn in (-1, 1):
            F.box(ir, uc + sgn * (w / 2 - 0.04), z + 1.55, 0.08, 3.0, depth / 2, depth)
        for k in range(int(w / 0.5)):
            F.box(
                ir, uc - w / 2 + 0.25 + k * 0.5, z + 1.55, 0.05, 3.0, depth - 0.05, 0.05
            )
    F.box(
        ir,
        uc + w / 2 - 0.3,
        z0 + floors * floor_h / 2,
        0.08,
        floors * floor_h,
        depth + 0.4,
        0.08,
    )


def street_context(kit, T, W, D, front_depth=6.0, side=5.0, ox=0.0, oy=0.0):
    """Sidewalk slab, granite curb and road strip in front of the building (z >= 0)."""
    ground, curb = T.get("ground"), T.get("curb")
    if not ground:
        return
    L = W + 2 * side
    y0 = -(D / 2) + oy
    kit.box(ground, (L, front_depth, 0.3), (ox, y0 - front_depth / 2, 0.15), bevel=0.0)
    for k in range(int(L / 5.0)):  # sidewalk joints
        kit.box(
            T.get("groove") or ground,
            (0.05, front_depth, 0.02),
            (ox - L / 2 + 2.5 + k * 5.0 - 0.0, y0 - front_depth / 2, 0.31),
            bevel=0.0,
        )
    if curb:
        kit.box(curb, (L, 0.6, 0.55), (ox, y0 - front_depth - 0.3, 0.275), bevel=0.0)
    if T.get("road"):
        kit.box(
            T["road"],
            (L, 9.0, 0.12),
            (ox, y0 - front_depth - 0.6 - 4.5, 0.06),
            bevel=0.0,
        )


# ------------------------------------------------------------------ half-timbering
def timber(F, T, z0, z1, ops, spacing=3.4, braces=True, out=0.1, th=0.2, tag="timber"):
    """Half-timber overlay on a wall: rails at top/bottom, studs between openings, diagonal braces."""
    L = F.L
    F.box(T[tag], 0, z0 + 0.12, L, 0.24, out, th)
    F.box(T[tag], 0, z1 - 0.12, L, 0.24, out, th)
    n = max(2, int(L / spacing))
    us = [-L / 2 + L * i / n for i in range(n + 1)]
    panels = []
    for a, b in zip(us, us[1:]):
        blocked = any(
            o.u0 - 0.6 < b and o.u1 + 0.6 > a and o.v1 > z0 and o.v0 < z1 for o in ops
        )
        panels.append((a, b, blocked))
    for u in us:
        inside = any(
            o.u0 - 0.5 < u < o.u1 + 0.5 and o.v1 > z0 and o.v0 < z1 for o in ops
        )
        if not inside:
            F.box(T[tag], u, (z0 + z1) / 2, 0.22, z1 - z0, out, th)
    if braces:
        for i, (a, b, blocked) in enumerate(panels):
            if blocked:
                continue
            dz = z1 - z0 - 0.5
            ln = math.hypot(b - a, dz)
            ang = math.atan2(dz, (b - a) if i % 2 == 0 else -(b - a))
            F.rbox(T[tag], (a + b) / 2, (z0 + z1) / 2, ln, 0.2, out, th - 0.02, ang)


def gable_timber(F, T, span, z_eave, rise, n=5, out=0.1, th=0.2, tag="timber"):
    """Studs and a collar beam inside a triangular gable end."""
    for i in range(1, n):
        u = -span / 2 + span * i / n
        h = rise * (1 - abs(u) / (span / 2)) - 0.3
        if h > 0.6:
            F.box(T[tag], u, z_eave + h / 2, 0.22, h, out, th)
    F.box(T[tag], 0, z_eave + 0.12, span, 0.24, out, th)
    F.box(T[tag], 0, z_eave + rise * 0.45, span * 0.55, 0.2, out, th)


def post(kit, tag, x, y, z0, z1, r=0.28, turned=True):
    """A turned porch post: shaft with collar knobs."""
    kit.cyl(tag, r, z1 - z0, (x, y, (z0 + z1) / 2), verts=10)
    if turned:
        for f in (0.15, 0.85):
            kit.box(tag, (r * 2.6, r * 2.6, 0.3), (x, y, z0 + (z1 - z0) * f), bevel=0.0)
        kit.box(tag, (r * 3.2, r * 3.2, 0.25), (x, y, z1 - 0.12), bevel=0.0)
        kit.box(tag, (r * 3.2, r * 3.2, 0.25), (x, y, z0 + 0.12), bevel=0.0)
