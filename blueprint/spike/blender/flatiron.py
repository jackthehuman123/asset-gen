"""
THROWAWAY SPIKE v2: photoreal-leaning Flatiron Building, modern-day NYC (new style: worlds/nyc).

  blender -b --factory-startup -P flatiron.py -- <spec.json> <out_dir> [--quick]

--quick: geometry only (tri counts per tag, workbench renders, no bake/export).

Finishes and wear are NOT in the spec: they come by name from the layered STYLE.md files named in
spec["style"] (game -> area), loaded with rbxasset.style.load_style (bpy-free). Materials are built with
the pipeline's tile-aware rbxasset/blender/finishes.make_finish:
  * spec["tiled"] tags get planar tile UVs (rbxasset/blender/tiling.tile_uvs, studs_per_tile from the
    game STYLE.md) and share one seamless 1024 px tile per finish (tiling.bake_tile), so pitting, mottle
    and rain streaks read at first-person range on a 270-stud building;
  * every other tag is smart-UV'd and uniquely baked (lib_pipeline.bake), so crevice grime shows.
Soot under ledges, block colour variation and street-level darkening are done by geometry choosing the
finish (`*_soot`, `*_b`, `limestone_street`), because tiles carry no position cues.

Coordinates: X east, Y north, Z up, 1 unit = 1 stud (~0.28 m).
  west = Fifth Avenue (x = 0), south = 22nd Street (y = 0), east = Broadway, rounded tip points north.
Geometry is accumulated per tag as raw vertex/face lists; a tag over budget is split by height.
"""

import json
import math
import os
import random
import sys
import time
from pathlib import Path

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import lib_pipeline as lp  # noqa: E402
from rbxasset.style import load_style  # noqa: E402
from rbxasset.blender import finishes as rfin  # noqa: E402
from rbxasset.blender import tiling  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
SPEC_PATH, OUT = argv[0], argv[1]
QUICK = "--quick" in argv
os.makedirs(OUT, exist_ok=True)
spec = json.load(open(SPEC_PATH))
if "finishes" in spec or "wear" in spec:
    raise SystemExit(
        "flatiron spec must not carry finishes/wear: they come from STYLE.md"
    )
style = load_style(
    Path(ROOT) / spec["style"]["game"], Path(ROOT) / spec["style"]["area"]
)
missing = sorted({f for f in spec["parts"].values() if f not in style.finishes})
if missing:
    raise SystemExit(f"parts use finishes not in STYLE.md: {missing}")
print(f"[flatiron] style: {style.intent_game!r} / {style.intent_area!r}")
print(
    f"[flatiron] lighting {style.lighting}, camera {style.camera}, studs_per_tile {style.studs_per_tile}, "
    f"budgets {style.budgets}"
)
MAX_TRIS = style.budgets["max_tris_per_mesh"]
SPLIT_AT = MAX_TRIS - 1000
TILED = set(spec.get("tiled", []))
STUDS = style.studs_per_tile

Fz = spec["flatiron"]
DMG = spec.get("damage", {})
DET = Fz["details"]
CH = DET["chamfer"]
rng = random.Random(DMG.get("seed", 1))
T0 = time.time()

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
Z = Vector((0, 0, 1))

# ------------------------------------------------------------------ geometry kernel
GEO = {k: ([], []) for k in spec["parts"]}


def newell(P):
    n = Vector((0, 0, 0))
    for i, a in enumerate(P):
        b = P[(i + 1) % len(P)]
        n.x += (a.y - b.y) * (a.z + b.z)
        n.y += (a.z - b.z) * (a.x + b.x)
        n.z += (a.x - b.x) * (a.y + b.y)
    return n


def add_solid(tag, pts, faces):
    """pts: list of Vectors; faces: [(index tuple, desired normal)] wound to face along the normal."""
    V, F = GEO[tag]
    b = len(V)
    V.extend(tuple(p) for p in pts)
    for ids, nrm in faces:
        ids = list(ids)
        if newell([pts[i] for i in ids]).dot(nrm) < 0:
            ids.reverse()
        F.append(tuple(b + i for i in ids))


def add_face(tag, pts, nrm):
    pts = [Vector(p) for p in pts]
    add_solid(tag, pts, [(range(len(pts)), nrm)])


def ccw(poly):
    a = sum(
        poly[i][0] * poly[(i + 1) % len(poly)][1]
        - poly[(i + 1) % len(poly)][0] * poly[i][1]
        for i in range(len(poly))
    )
    return poly if a > 0 else poly[::-1]


def prism(tag, poly, z0, z1, top=True, bottom=True):
    poly = ccw(poly)
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        d = Vector((x1 - x0, y1 - y0, 0))
        if d.length < 1e-4:
            continue
        add_face(
            tag,
            [(x0, y0, z0), (x1, y1, z0), (x1, y1, z1), (x0, y0, z1)],
            Vector((d.y, -d.x, 0)),
        )
    if top:
        add_face(tag, [(x, y, z1) for x, y in poly], Z)
    if bottom:
        add_face(tag, [(x, y, z0) for x, y in poly], -Z)


# ------------------------------------------------------------------ footprint (exact offsets)
A, YD, R = Fz["south_width"], Fz["depth"], Fz["tip_radius"]
LE = math.hypot(A, YD)
NE = Vector((YD / LE, A / LE, 0))  # Broadway outward normal
CE = YD * A / LE
CX, CY = R, (A * YD - YD * R - R * LE) / A  # tip arc centre
AE = math.atan2(NE.y, NE.x)  # arc runs AE..pi
AM = (AE + math.pi) / 2


def footprint(o, n_arc=14):
    SW = (-o, -o)
    SE = ((CE + o + NE.y * o) / NE.x, -o)
    arc = [
        (CX + (R + o) * math.cos(a), CY + (R + o) * math.sin(a))
        for a in (AE + (math.pi - AE) * t / (n_arc - 1) for t in range(n_arc))
    ]
    return [SW, SE] + arc


def course(tag, o, z0, z1, ch=0.12, n_arc=14, bottom=True):
    """Chamfered horizontal course following the footprint at offset o (exact offsets, same vertex count)."""
    ch = min(ch, (z1 - z0) * 0.3)
    P0, P1 = ccw(footprint(o - ch, n_arc)), ccw(footprint(o, n_arc))
    rings = (
        [(P0, z0), (P1, z0 + ch), (P1, z1 - ch), (P0, z1)]
        if ch > 0
        else [(P1, z0), (P1, z1)]
    )
    n = len(P1)
    for r in range(len(rings) - 1):
        (Pa, za), (Pb, zb) = rings[r], rings[r + 1]
        for i in range(n):
            j = (i + 1) % n
            d = Vector((P1[j][0] - P1[i][0], P1[j][1] - P1[i][1], 0))
            if d.length < 1e-4:
                continue
            out = Vector((d.y, -d.x, 0)).normalized()
            nz = 0 if za + ch < zb - 1e-6 or ch == 0 else (-1 if r == 0 else 1)
            add_face(
                tag,
                [(*Pa[i], za), (*Pa[j], za), (*Pb[j], zb), (*Pb[i], zb)],
                out + Z * nz,
            )
    top = rings[-1][0]
    add_face(tag, [(x, y, z1) for x, y in top], Z)
    if bottom:
        add_face(tag, [(x, y, z0) for x, y in rings[0][0]], -Z)


def cross2(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def clip_left(poly, a, b):
    out = []
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]
        sp, sq = cross2(a, b, p), cross2(a, b, q)
        if sp >= 0:
            out.append(p)
        if (sp >= 0) != (sq >= 0):
            t = sp / (sp - sq)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def hull(pts):
    pts = sorted(set(pts))
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross2(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross2(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def inside(poly, p):
    poly = ccw(poly)
    return all(
        cross2(poly[i], poly[(i + 1) % len(poly)], p) >= 0 for i in range(len(poly))
    )


def area(poly):
    return (
        abs(
            sum(
                poly[i][0] * poly[(i + 1) % len(poly)][1]
                - poly[(i + 1) % len(poly)][0] * poly[i][1]
                for i in range(len(poly))
            )
        )
        / 2
    )


def perimeter_walk(poly, step, offset=0.0):
    poly = ccw(poly)
    n, carry = len(poly), offset
    for i in range(n):
        p, q = Vector((*poly[i], 0)), Vector((*poly[(i + 1) % n], 0))
        d = q - p
        L = d.length
        if L < 1e-6:
            continue
        t = d / L
        nrm = Vector((t.y, -t.x, 0))
        s = carry
        while s < L:
            yield p + t * s, t, nrm
            s += step
        carry = s - L


# ------------------------------------------------------------------ facade frames
class Facade:
    """Local coords: u along the face (from its south end), v = world Z, w = outward."""

    def __init__(self, name, origin, U, N, length, oriels=()):
        self.name, self.O, self.U, self.N, self.L = (
            name,
            Vector(origin),
            Vector(U).normalized(),
            Vector(N).normalized(),
            length,
        )
        n = max(1, round(length / Fz["bay_target"]))
        b = length / n
        self.b = b
        cp, pw = Fz["corner_pier"], Fz["pier"]
        self.piers = (
            [(0.0, cp)]
            + [(k * b - pw / 2, k * b + pw / 2) for k in range(1, n)]
            + [(length - cp, length)]
        )
        self.bays = []
        for i in range(n):
            el = cp if i == 0 else i * b + pw / 2
            er = length - cp if i == n - 1 else (i + 1) * b - pw / 2
            self.bays.append((el, er, i))
        self.oriels = [(i0 * b, (i1 + 1) * b) for i0, i1 in oriels]

    def bulge(self, u):
        for u0, u1 in self.oriels:
            if u0 < u < u1:
                return Fz["oriels"]["depth"] * min(
                    1.0, 1.6 * math.sin(math.pi * (u - u0) / (u1 - u0))
                )
        return 0.0

    def P(self, u, v, w):
        return self.O + self.U * u + Z * v + self.N * w

    def box(self, tag, u0, u1, v0, v1, w0, w1, skip=("w-",), ch=0.0):
        """Box in facade space; ch > 0 chamfers the four front (w+) edges."""
        ch = min(ch, 0.3 * (u1 - u0), 0.3 * (v1 - v0), 0.45 * (w1 - w0))
        U, N = self.U, self.N
        if ch <= 0.005:
            pts = [
                self.P((u0, u1)[i], (v0, v1)[j], (w0, w1)[k])
                for i in (0, 1)
                for j in (0, 1)
                for k in (0, 1)
            ]
            idx = lambda i, j, k: i * 4 + j * 2 + k  # noqa: E731
            faces = {
                "u-": ([idx(0, 0, 0), idx(0, 1, 0), idx(0, 1, 1), idx(0, 0, 1)], -U),
                "u+": ([idx(1, 0, 0), idx(1, 1, 0), idx(1, 1, 1), idx(1, 0, 1)], U),
                "v-": ([idx(0, 0, 0), idx(1, 0, 0), idx(1, 0, 1), idx(0, 0, 1)], -Z),
                "v+": ([idx(0, 1, 0), idx(1, 1, 0), idx(1, 1, 1), idx(0, 1, 1)], Z),
                "w-": ([idx(0, 0, 0), idx(1, 0, 0), idx(1, 1, 0), idx(0, 1, 0)], -N),
                "w+": ([idx(0, 0, 1), idx(1, 0, 1), idx(1, 1, 1), idx(0, 1, 1)], N),
            }
            add_solid(tag, pts, [f for k_, f in faces.items() if k_ not in skip])
            return
        us, vs = (u0, u1), (v0, v1)
        pts = []
        for i in (0, 1):  # 0..3 back, 4..7 mid ring, 8..11 front (inset)
            for j in (0, 1):
                pts.append(self.P(us[i], vs[j], w0))
        for i in (0, 1):
            for j in (0, 1):
                pts.append(self.P(us[i], vs[j], w1 - ch))
        for i in (0, 1):
            for j in (0, 1):
                pts.append(
                    self.P(
                        us[i] + (ch if i == 0 else -ch),
                        vs[j] + (ch if j == 0 else -ch),
                        w1,
                    )
                )
        b_, m_, f_ = (
            (lambda i, j: i * 2 + j),
            (lambda i, j: 4 + i * 2 + j),
            (lambda i, j: 8 + i * 2 + j),
        )
        faces = [
            ([f_(0, 0), f_(1, 0), f_(1, 1), f_(0, 1)], N),
            ([m_(0, 0), m_(1, 0), f_(1, 0), f_(0, 0)], N - Z),
            ([m_(0, 1), m_(1, 1), f_(1, 1), f_(0, 1)], N + Z),
            ([m_(0, 0), m_(0, 1), f_(0, 1), f_(0, 0)], N - U),
            ([m_(1, 0), m_(1, 1), f_(1, 1), f_(1, 0)], N + U),
        ]
        sides = {
            "u-": ([b_(0, 0), b_(0, 1), m_(0, 1), m_(0, 0)], -U),
            "u+": ([b_(1, 0), b_(1, 1), m_(1, 1), m_(1, 0)], U),
            "v-": ([b_(0, 0), b_(1, 0), m_(1, 0), m_(0, 0)], -Z),
            "v+": ([b_(0, 1), b_(1, 1), m_(1, 1), m_(0, 1)], Z),
            "w-": ([b_(0, 0), b_(1, 0), b_(1, 1), b_(0, 1)], -N),
        }
        faces += [f for k_, f in sides.items() if k_ not in skip]
        add_solid(tag, pts, faces)

    def quad(self, tag, u0, u1, v0, v1, w):
        add_face(
            tag,
            [
                self.P(u0, v0, w),
                self.P(u1, v0, w),
                self.P(u1, v1, w),
                self.P(u0, v1, w),
            ],
            self.N,
        )

    def cyl(self, tag, u, v0, v1, w, r, n=8):
        """Vertical round shaft (colonnette, pole) centred at (u, w)."""
        for s in range(n):
            a, b = 2 * math.pi * s / n, 2 * math.pi * (s + 1) / n
            m = (a + b) / 2
            p = lambda ang, v: self.P(u + r * math.cos(ang), v, w + r * math.sin(ang))  # noqa: E731
            add_face(
                tag,
                [p(a, v0), p(b, v0), p(b, v1), p(a, v1)],
                self.U * math.cos(m) + self.N * math.sin(m),
            )

    def wreath(self, tag, u, v, w, r, n=10):
        """Medallion: raised disc inside a projecting ring (wreath), facing out of the facade."""

        def p(rad, ang, ww):
            return self.P(u + rad * math.cos(ang), v + rad * math.sin(ang), ww)

        rin, rout = r * 0.62, r
        for s in range(n):
            a, b = 2 * math.pi * s / n, 2 * math.pi * (s + 1) / n
            m = (a + b) / 2
            radial = self.U * math.cos(m) + Z * math.sin(m)
            add_face(
                tag,
                [
                    p(rin, a, w + 0.35),
                    p(rout, a, w + 0.35),
                    p(rout, b, w + 0.35),
                    p(rin, b, w + 0.35),
                ],
                self.N,
            )  # ring face
            add_face(
                tag,
                [
                    p(rout, a, w),
                    p(rout, b, w),
                    p(rout, b, w + 0.35),
                    p(rout, a, w + 0.35),
                ],
                radial,
            )
            add_face(
                tag,
                [
                    p(rin, a, w + 0.2),
                    p(rin, b, w + 0.2),
                    p(rin, b, w + 0.35),
                    p(rin, a, w + 0.35),
                ],
                -radial,
            )
        add_face(
            tag, [p(rin, 2 * math.pi * s / n, w + 0.2) for s in range(n)], self.N
        )  # inner disc

    def sash(self, tag, a, b, v0, v1, w, fw=0.22, rail=True):
        """Window sash frame (front ring) + meeting rail, sitting just in front of the glass at w."""
        o = [
            self.P(a, v0, w + 0.12),
            self.P(b, v0, w + 0.12),
            self.P(b, v1, w + 0.12),
            self.P(a, v1, w + 0.12),
        ]
        i = [
            self.P(a + fw, v0 + fw, w + 0.12),
            self.P(b - fw, v0 + fw, w + 0.12),
            self.P(b - fw, v1 - fw, w + 0.12),
            self.P(a + fw, v1 - fw, w + 0.12),
        ]
        add_solid(
            tag,
            o + i,
            [((k, (k + 1) % 4, 4 + (k + 1) % 4, 4 + k), self.N) for k in range(4)],
        )
        if rail:
            vm = (v0 + v1) / 2
            self.box(
                tag,
                a + fw,
                b - fw,
                vm - 0.1,
                vm + 0.1,
                w,
                w + 0.1,
                skip=("w-", "u-", "u+"),
            )


TIP_T = Vector((CX, CY, 0)) + NE * R
SE3 = Vector((A, 0, 0))
south = Facade("south", (0, 0, 0), (1, 0, 0), (0, -1, 0), A)
east = Facade("east", SE3, TIP_T - SE3, NE, (TIP_T - SE3).length, Fz["oriels"]["east"])
west = Facade("west", (0, 0, 0), (0, 1, 0), (-1, 0, 0), CY, Fz["oriels"]["west"])
FACADES = (south, east, west)
print(
    f"[flatiron] footprint: south {A:.1f}, Broadway {east.L:.1f} ({len(east.bays)} bays), "
    f"Fifth Ave {west.L:.1f} ({len(west.bays)} bays), tip r={R} at y={CY + R:.1f}, "
    f"angle {math.degrees(math.atan2(A, YD)):.1f} deg"
)


# ------------------------------------------------------------------ tip (rounded arc) pieces
def arc_band(tag, r0, r1, a0, a1, z0, z1, n, faces=("out", "top", "bot", "ends")):
    def pt(r, a, z):
        return (CX + r * math.cos(a), CY + r * math.sin(a), z)

    angs = [a0 + (a1 - a0) * t / n for t in range(n + 1)]
    for i in range(n):
        a, b = angs[i], angs[i + 1]
        m = (a + b) / 2
        rad = Vector((math.cos(m), math.sin(m), 0))
        if "out" in faces:
            add_face(
                tag, [pt(r1, a, z0), pt(r1, b, z0), pt(r1, b, z1), pt(r1, a, z1)], rad
            )
        if "in" in faces:
            add_face(
                tag, [pt(r0, a, z0), pt(r0, b, z0), pt(r0, b, z1), pt(r0, a, z1)], -rad
            )
        if "top" in faces:
            add_face(
                tag, [pt(r0, a, z1), pt(r1, a, z1), pt(r1, b, z1), pt(r0, b, z1)], Z
            )
        if "bot" in faces:
            add_face(
                tag, [pt(r0, a, z0), pt(r1, a, z0), pt(r1, b, z0), pt(r0, b, z0)], -Z
            )
    if "ends" in faces:
        for a, sgn in ((a0, -1), (a1, 1)):
            t = Vector((-math.sin(a), math.cos(a), 0)) * sgn
            add_face(
                tag, [pt(r0, a, z0), pt(r1, a, z0), pt(r1, a, z1), pt(r0, a, z1)], t
            )


DELTA = 1.3 / R
SU, HD, MUL = Fz["sill_up"], Fz["head_down"], Fz["mullion"]
G = Fz["rustication"]["channel"]


def tip_window(wall, z0, z1):
    arc_band(
        wall, R - 0.9, R + 0.35, AM - DELTA - 0.1, AM + DELTA + 0.1, z0 - 0.45, z0, 3
    )  # sill
    arc_band(
        wall,
        R - 0.9,
        R + 0.2,
        AM - DELTA - 0.1,
        AM + DELTA + 0.1,
        z1 - 0.45,
        z1 + 0.35,
        3,
    )  # hood
    arc_band(
        "glass",
        R - 0.6,
        R - 0.6,
        AM - DELTA,
        AM + DELTA,
        z0,
        z1 - 0.45,
        3,
        faces=("out",),
    )
    arc_band(
        "sash",
        R - 0.5,
        R - 0.5,
        AM - DELTA,
        AM + DELTA,
        (z0 + z1) / 2 - 0.3,
        (z0 + z1) / 2 - 0.1,
        3,
        faces=("out", "top"),
    )


def tip_piers(tag, z0, z1, r_out=R):
    arc_band(tag, R - 1.0, r_out, AE, AM - DELTA, z0, z1, 5, faces=("out", "ends"))
    arc_band(tag, R - 1.0, r_out, AM + DELTA, math.pi, z0, z1, 5, faces=("out", "ends"))


def tip_band(tag, z0, z1, r_out=R - 0.25, faces=("out", "top", "bot")):
    arc_band(tag, R - 1.0, r_out, AE, math.pi, z0, z1, 12, faces=faces)


# ------------------------------------------------------------------ shared window
def window(fc, wall, a, b, s, h, bw, hood_ch=CH, keystone=False):
    """Opening [a,b] x [s,h] on facade plane bw: jambs, chamfered hood, recessed glass, sash.
    The sill is part of the floor's string course (see sill_course)."""
    jw = 0.35
    fc.box(wall, a, a + jw, s, h - 0.45, bw - 1.0, bw - 0.1, skip=("w-", "v-", "v+"))
    fc.box(wall, b - jw, b, s, h - 0.45, bw - 1.0, bw - 0.1, skip=("w-", "v-", "v+"))
    fc.box(wall, a - 0.2, b + 0.2, h - 0.45, h + 0.35, bw - 1.0, bw + 0.22, ch=hood_ch)
    if keystone:
        c = (a + b) / 2
        fc.box(
            wall, c - 0.45, c + 0.45, h - 0.6, h + 0.9, bw - 0.5, bw + 0.45, ch=hood_ch
        )
    gw = bw - 0.65  # glass ~0.55 behind the surround face
    fc.quad("glass", a + jw, b - jw, s, h - 0.45, gw)
    fc.sash("sash", a + jw, b - jw, s, h - 0.45, gw)


def sill_course(fc, wall, u0, u1, s, bw, ch=CH):
    fc.box(wall, u0, u1, s - 0.45, s, bw - 1.0, bw + 0.35, ch=ch)


# ------------------------------------------------------------------ levels
ZG = Fz["ground_floor"]
BFH, NB = Fz["base_floor_height"], Fz["base_floors"]
ZB = ZG + NB * BFH
SFH = Fz["shaft_floor_height"]
SHAFT_LINES = [ZB + k * SFH for k in range(Fz["shaft_floors"] + 1)]
ZS = SHAFT_LINES[-1]
Z19 = ZS + Fz["crown_floor_height"]
ZA0 = Z19 + SU - HD
ZAT = ZA0 + Fz["arcade_height"] - (SU - HD)
CO = Fz["cornice"]
ZC = ZAT + CO["height"]
ZP = ZC + Fz["parapet"]
PH = Fz["penthouse"]
ZPH = ZC + PH["height"]
AN = Fz["annex"]
Y_ANNEX = CY - AN["back"]


def under_annex(fc, u):
    """True where the cowcatcher annex wraps this facade (its ground floor is inside the annex)."""
    if fc is south:
        return False
    return (fc.P(u, 0, 0)).y > Y_ANNEX - 0.5


# ------------------------------------------------------------------ ground floor: rusticated piers + storefronts
SF = Fz["storefront"]
SB0, SB1 = SF["sign_band"]
AW_TOP = SB0 - 0.1
awning_count = 0


def awning(fc, u0, u1, top, drop, proj):
    us, ws = (u0, u1), (-0.4, proj)

    def corner(i, j, k):
        z = top - drop * (k == 1) - 0.15 * j
        return fc.P(us[i], z, ws[k])

    pts = [corner(i, j, k) for i in (0, 1) for j in (0, 1) for k in (0, 1)]
    ctr = sum(pts, Vector()) / 8
    quads = [
        (0, 2, 3, 1),
        (4, 5, 7, 6),
        (0, 1, 5, 4),
        (2, 6, 7, 3),
        (0, 4, 6, 2),
        (1, 3, 7, 5),
    ]
    add_solid(
        "awnings",
        pts,
        [(q, sum((pts[i] for i in q), Vector()) / 4 - ctr) for q in quads],
    )
    fc.box(
        "awnings", u0, u1, top - drop - 0.9, top - drop, proj - 0.08, proj, skip=()
    )  # valance
    for u in us:  # side cheeks
        cheek = [
            fc.P(u, top, -0.4),
            fc.P(u, top - drop, proj),
            fc.P(u, top - drop - 0.9, proj),
        ]
        add_face("awnings", cheek, fc.U if u == u1 else -fc.U)
    for u in (u0 + 0.3, u1 - 0.3):  # iron arms
        fc.box(
            "signage",
            u - 0.06,
            u + 0.06,
            top - drop - 0.1,
            top - drop + 0.05,
            -0.4,
            proj - 0.1,
            skip=("w-",),
        )


for fc in FACADES:
    for pu0, pu1 in fc.piers:
        fc.box(
            "ground_soot",
            pu0 - 0.12,
            pu1 + 0.12,
            0,
            0.9,
            -1.0,
            0.2,
            skip=("w-", "v-"),
            ch=0.12,
        )  # plinth
        fc.box(
            "ground_soot", pu0, pu1, 0.9, SB1, -1.0, -0.55, skip=("w-", "v-", "v+")
        )  # channel
        pitch = (SB1 - 0.9) / 4
        for k in range(4):
            fc.box(
                "ground_stone",
                pu0,
                pu1,
                0.9 + k * pitch + G / 2,
                0.9 + (k + 1) * pitch - G / 2,
                -0.8,
                0.0,
                ch=0.22,
            )
    u = 0.0
    while u < fc.L - 0.1:  # jointed lintel band
        ln = min(rng.uniform(3.5, 5.5), fc.L - u)
        fc.box(
            "ground_stone",
            u + 0.06,
            u + ln - 0.06,
            SB1 + 0.05,
            ZG - 0.65,
            -1.0,
            -0.1,
            ch=CH,
        )
        u += ln
    fc.box("ground_soot", 0, fc.L, SB1, ZG - 0.6, -1.0, -0.35, skip=("w-", "v-", "v+"))
    for el, er, i in fc.bays:
        if under_annex(fc, (el + er) / 2):
            fc.quad("ground_soot", el, er, 0, SB1, -1.2)
            continue
        third = (er - el) / 3
        door = i % 3 == 1
        T = SF["transom"]
        fc.box("mullions", el, er, SB0 - 0.3, SB0, -1.5, -1.0, skip=("w-",))  # head
        for u in (el, er):
            fc.box(
                "mullions",
                u - 0.01 if u == el else u - 0.26,
                u + 0.26 if u == el else u + 0.01,
                0,
                SB0,
                -1.5,
                -1.0,
                skip=("w-",),
            )
        fc.quad("glass", el, er, T + 0.25, SB0 - 0.3, -1.3)  # transom glass
        fc.box("mullions", el, er, T, T + 0.25, -1.5, -1.05, skip=("w-",))
        for k in (1, 2):
            u = el + k * third
            fc.box(
                "mullions",
                u - 0.12,
                u + 0.12,
                0.0 if door else 0.9,
                SB0 - 0.3,
                -1.5,
                -1.05,
                skip=("w-",),
            )
        for k in range(3):
            a, b = el + k * third, el + (k + 1) * third
            if door and k == 1:  # recessed door
                d = 2.4
                fc.quad("glass", a + 0.12, b - 0.12, 0.0, T, -1.3 - d)
                fc.box(
                    "mullions",
                    a + 0.12,
                    b - 0.12,
                    T - 0.25,
                    T,
                    -1.5 - d,
                    -1.3 - d + 0.1,
                    skip=("w-",),
                )
                for uu in (a + 0.12, b - 0.12):
                    fc.box(
                        "mullions",
                        uu - 0.1,
                        uu + 0.1,
                        0,
                        T,
                        -1.5 - d,
                        -1.25 - d,
                        skip=("w-",),
                    )
                fc.box(
                    "mullions",
                    a + 0.6,
                    b - 0.6,
                    3.6,
                    3.85,
                    -1.25 - d,
                    -1.05 - d,
                    skip=("w-",),
                )  # push bar
                for uu, nrm in ((a + 0.12, fc.U), (b - 0.12, -fc.U)):  # glass returns
                    add_face(
                        "glass",
                        [
                            fc.P(uu, 0, -1.3),
                            fc.P(uu, 0, -1.3 - d),
                            fc.P(uu, T, -1.3 - d),
                            fc.P(uu, T, -1.3),
                        ],
                        nrm,
                    )
                add_face(
                    "mullions",
                    [
                        fc.P(a + 0.12, T, -1.3),
                        fc.P(b - 0.12, T, -1.3),
                        fc.P(b - 0.12, T, -1.3 - d),
                        fc.P(a + 0.12, T, -1.3 - d),
                    ],
                    -Z,
                )
            else:
                fc.box("mullions", a, b, 0, 0.9, -1.5, -1.0, skip=("w-",))  # bulkhead
                fc.quad("glass", a, b, 0.9, T, -1.3)
        # blank sign band (no text, no logo) with a raised frame and a shadow lip
        fc.box("signage", el, er, SB0, SB1, -1.0, -0.45, skip=("w-", "v+"))
        for v0, v1 in ((SB0, SB0 + 0.25), (SB1 - 0.25, SB1)):
            fc.box("signage", el, er, v0, v1, -1.0, -0.25, skip=("w-",))
        if rng.random() < DMG.get("awning_fraction", 0.5):
            awning_count += 1
            awning(
                fc,
                el + 0.15,
                er - 0.15,
                AW_TOP,
                SF["awning_drop"],
                SF["awning_projection"],
            )
course("ground_stone", 1.0, ZG - 0.6, ZG + 0.6, CH)  # belt course
tip_band("ground_stone", SB1, ZG - 0.6, R - 0.1)

# ------------------------------------------------------------------ floors 2-4: rusticated base (V-jointed blocks)
BASE_FAM = ("base_stone", "base_stone_b")
for fc in FACADES:
    for pu0, pu1 in fc.piers:
        fc.box(
            "base_soot",
            pu0 + 0.05,
            pu1 - 0.05,
            ZG + 0.6,
            ZB - HD,
            -1.0,
            -0.6,
            skip=("w-", "v-", "v+"),
        )
    for k in range(NB):
        z0, z1 = ZG + k * BFH, ZG + (k + 1) * BFH
        s, h = z0 + SU, z1 - HD
        lo = ZG + 0.6 if k == 0 else z0 - HD + 0.35
        fc.box(
            "base_soot", 0, fc.L, lo, s - 0.45, -1.0, -0.6, skip=("w-", "v-", "v+")
        )  # course backing
        u = 0.0
        while u < fc.L - 0.1:  # course blocks
            ln = min(rng.uniform(3.2, 5.2), fc.L - u)
            fc.box(
                rng.choice(BASE_FAM),
                u + G / 4,
                u + ln - G / 4,
                lo + G / 2,
                s - 0.45 - G / 2,
                -0.7,
                0.0,
                ch=0.22,
            )
            u += ln
        half = (h - s) / 2
        for pu0, pu1 in fc.piers:
            for va, vb in ((s, s + half), (s + half, h - 0.45)):
                fc.box(
                    rng.choice(BASE_FAM),
                    pu0,
                    pu1,
                    va + G / 2,
                    vb - G / 2,
                    -0.7,
                    0.0,
                    ch=0.22,
                )
        for el, er, i in fc.bays:
            mid = (el + er) / 2
            fc.box(
                "base_stone",
                mid - MUL / 2,
                mid + MUL / 2,
                s,
                h - 0.45,
                -1.0,
                -0.25,
                skip=("w-", "v-", "v+"),
                ch=0.1,
            )
            for a, b in ((el, mid - MUL / 2), (mid + MUL / 2, er)):
                fc.box(
                    "base_stone", a - 0.3, b + 0.3, s - 0.45, s, -1.0, 0.35, ch=CH
                )  # sill
                window(fc, "base_stone", a, b, s, h, -0.05, keystone=True)
for k in range(NB):
    z0, z1 = ZG + k * BFH, ZG + (k + 1) * BFH
    s, h = z0 + SU, z1 - HD
    lo = ZG + 0.6 if k == 0 else z0 - HD + 0.35
    tip_band("base_stone", lo + G / 2, s - 0.45 - G / 2, R)
    half = (h - s) / 2
    tip_piers("base_stone", s + G / 2, s + half - G / 2)
    tip_piers("base_stone_b", s + half + G / 2, h - 0.45 - G / 2)
    tip_window("base_stone", s, h)
tip_band("base_soot", ZG + 0.6, ZB - HD, R - 0.6, faces=("out",))

# ------------------------------------------------------------------ balcony over the base
course("base_soot", 0.9, ZB - 1.4, ZB - 0.6, 0.0)  # sooted frieze
course("balcony", 0.6, ZB - 1.4, ZB - 1.0, 0.1)  # bed moulding
for p, t, nrm in perimeter_walk(footprint(0.0, 30), 2.2, 1.0):  # modillions
    Facade("m", p, t, nrm, 1).box(
        "balcony", -0.3, 0.3, ZB - 0.9, ZB - 0.2, 0.7, 2.6, skip=("w-", "v+"), ch=0.08
    )
course("balcony", 2.9, ZB - 0.2, ZB + 0.6, CH)  # corona
course("balcony", 2.6, ZB + 0.6, ZB + 0.9, 0.06)  # balustrade plinth
for p, t, nrm in perimeter_walk(footprint(2.25, 30), 0.95, 0.5):  # balusters
    Facade("b", p, t, nrm, 1).box(
        "balcony", -0.17, 0.17, ZB + 0.9, ZB + 2.2, -0.17, 0.17, skip=("v-", "v+")
    )
course("balcony", 2.6, ZB + 2.2, ZB + 2.6, 0.08, bottom=True)  # handrail
# the handrail's solid footprint would roof the building at ZB+2.6: lift the shaft's inner wall behind it
ZSH0 = ZB + 0.6

# ------------------------------------------------------------------ shaft: paired windows, oriels, ornament
WIN_CANDIDATES = []
NF = Fz["shaft_floors"]
for f in range(NF):
    z0, z1 = SHAFT_LINES[f], SHAFT_LINES[f + 1]
    s, h = z0 + SU, z1 - HD
    last = f == NF - 1
    s_next_bot = (
        ZS - 0.8 if last else z1 + SU - 0.45
    )  # bottom of the next string course
    band = f in Fz["band_floors"]
    for fc in FACADES:
        for pu0, pu1 in fc.piers:
            pc = (pu0 + pu1) / 2
            bwp = fc.bulge(pc)
            fam = "shaft_wall" if rng.random() < 0.6 else "shaft_wall_b"
            lo = ZSH0 if f == 0 else s
            fc.box(
                fam, pu0, pu1, lo, s_next_bot, -1.0, bwp, skip=("w-", "v-", "v+"), ch=CH
            )
            if f == 0:
                pass
            sill_course(fc, "shaft_wall", pu0, pu1, s, bwp)
            if band and not last and pu1 - pu0 < 3:
                fc.wreath("shaft_wall", pc, (h + 0.35 + s_next_bot) / 2, bwp, 0.95)
        for el, er, i in fc.bays:
            mid = (el + er) / 2
            bwm = fc.bulge(mid)
            lo = ZSH0 if f == 0 else s
            fc.box(
                "shaft_wall",
                mid - MUL / 2,
                mid + MUL / 2,
                lo,
                s_next_bot,
                -1.0,
                bwm - 0.08,
                skip=("w-", "v-", "v+"),
                ch=0.1,
            )  # pilaster strip
            flat = max(fc.bulge(el), fc.bulge(mid), fc.bulge(er)) == 0.0
            if flat:  # one course piece per bay
                sill_course(fc, "shaft_wall", el, er, s, 0.0)
            else:
                sill_course(fc, "shaft_wall", mid - MUL / 2, mid + MUL / 2, s, bwm)
            for a, b in ((el, mid - MUL / 2), (mid + MUL / 2, er)):
                bw = fc.bulge((a + b) / 2)
                if not flat:
                    sill_course(fc, "shaft_wall", a, b, s, bw)
                window(fc, "shaft_wall", a, b, s, h, bw, hood_ch=CH if s < 100 else 0.0)
                WIN_CANDIDATES.append((fc, a, b, s, bw))
                spans = []
                if f == 0:
                    spans.append((ZSH0, s - 0.45))
                if not last:
                    spans.append((h + 0.35, s_next_bot))
                for zl, zh in spans:  # sooted spandrels
                    fc.quad("shaft_soot", a, b, zl, zh, bw - 0.45)
                    if zh - zl > 1.4:
                        fc.box(
                            "shaft_soot",
                            a + 0.45,
                            b - 0.45,
                            zl + 0.4,
                            zh - 0.4,
                            bw - 0.5,
                            bw - 0.2,
                            ch=0.08 if z0 < 90 else 0.0,
                        )
    tip_piers("shaft_wall", s, s_next_bot)
    if f == 0:
        tip_piers("shaft_wall", ZSH0, s - 0.45)
        tip_band("shaft_soot", ZSH0, s - 0.45, R - 0.45, faces=("out",))
    arc_band("shaft_wall", R - 1.0, R + 0.35, AE, math.pi, s - 0.45, s, 12)
    if not last:
        tip_band("shaft_soot", h + 0.35, s_next_bot, R - 0.45, faces=("out",))
    tip_window("shaft_wall", s, h)

# window AC units on a few shaft windows (modern street life, deterministic from the seed)
for fc, a, b, zs_, bw in rng.sample(WIN_CANDIDATES, DMG.get("ac_units", 0)):
    c = (a + b) / 2
    fc.box(
        "ac_units",
        c - 1.1,
        c + 1.1,
        zs_ + 0.05,
        zs_ + 1.6,
        bw - 0.9,
        bw + 1.3,
        skip=("w-",),
        ch=0.06,
    )
    fc.box(
        "ac_units",
        c - 0.95,
        c + 0.95,
        zs_ + 0.2,
        zs_ + 1.45,
        bw + 1.3,
        bw + 1.36,
        skip=("w-",),
    )
    fc.box(
        "ac_units",
        c - 1.15,
        c - 0.95,
        zs_ - 0.9,
        zs_ + 0.05,
        bw - 0.4,
        bw + 1.2,
        skip=("w-",),
    )

# ------------------------------------------------------------------ crown: floor 19 + arched arcade on colonnettes
course("crown_wall", 2.2, ZS - 0.8, ZS + 1.0, CH)
course("crown_wall", 2.6, ZS + 1.0, ZS + 1.4, 0.08)
course("crown_wall", 0.7, ZA0 - 0.7, ZA0, 0.1)  # arcade sill course
for fc in FACADES:
    for pu0, pu1 in fc.piers:
        pc = (pu0 + pu1) / 2
        fc.box(
            "crown_wall",
            pu0,
            pu1,
            ZS + 1.4,
            ZAT,
            -1.0,
            0.0,
            skip=("w-", "v-", "v+"),
            ch=CH,
        )
        fc.box(
            "crown_wall",
            pu0 - 0.25,
            pu1 + 0.25,
            ZAT - 2.6,
            ZAT - 1.9,
            -1.0,
            0.35,
            skip=("w-",),
            ch=0.1,
        )
        fc.box(
            "crown_wall",
            pu0 - 0.15,
            pu1 + 0.15,
            ZAT - 1.9,
            ZAT,
            -1.0,
            0.25,
            skip=("w-", "v+"),
            ch=0.1,
        )
        if pu1 - pu0 < 3:
            fc.wreath("crown_wall", pc, ZA0 + 6.5, 0.0, 0.9)
    for el, er, i in fc.bays:
        mid = (el + er) / 2
        fc.box(
            "crown_wall",
            mid - MUL / 2,
            mid + MUL / 2,
            ZS + 1.4,
            ZA0 - 0.7,
            -1.0,
            -0.08,
            skip=("w-", "v-", "v+"),
            ch=0.1,
        )
        s, h = ZS + SU, Z19 - HD
        sill_course(fc, "crown_wall", mid - MUL / 2, mid + MUL / 2, s, 0.0)
        for a, b in ((el, mid - MUL / 2), (mid + MUL / 2, er)):
            sill_course(fc, "crown_wall", a, b, s, 0.0)
            window(fc, "crown_wall", a, b, s, h, 0.0)
            fc.quad("crown_soot", a, b, ZS + 1.4, s - 0.45, -0.45)
        fc.quad("crown_soot", el, er, h + 0.35, ZA0 - 0.7, -0.45)
        # arcade: one round arch over each window pair, carried on a colonnette
        RA = (er - el) / 2
        zsp = ZAT - RA - 1.0
        fc.box(
            "crown_wall",
            mid - 0.5,
            mid + 0.5,
            ZA0,
            ZA0 + 0.6,
            -0.9,
            0.05,
            skip=("w-", "v-"),
            ch=0.08,
        )
        fc.cyl("crown_wall", mid, ZA0 + 0.6, zsp - 0.7, -0.45, 0.38, 8)
        fc.box(
            "crown_wall",
            mid - 0.6,
            mid + 0.6,
            zsp - 0.7,
            zsp,
            -0.95,
            0.15,
            skip=("w-",),
            ch=0.1,
        )
        zt0 = (ZA0 + zsp) / 2
        fc.box(
            "sash", el, er, zt0 - 0.3, zt0 + 0.3, -1.0, -0.4, skip=("w-",)
        )  # transom bar
        for a, b in ((el, mid - 0.4), (mid + 0.4, er)):
            fc.quad("glass", a, b, ZA0, zsp, -0.75)
            fc.sash("sash", a, b, ZA0, zsp, -0.75, rail=False)
        n = 8
        arc = [
            (
                mid + RA * math.cos(math.pi * s_ / n),
                zsp + RA * math.sin(math.pi * s_ / n),
            )
            for s_ in range(n + 1)
        ]
        for s_ in range(n):
            add_face(
                "glass",
                [
                    fc.P(mid, zsp, -0.75),
                    fc.P(*arc[s_], -0.75),
                    fc.P(*arc[s_ + 1], -0.75),
                ],
                fc.N,
            )
        wf, wb = -0.25, -1.0
        apex = arc[n // 2]
        for side_pts, corner in (
            (arc[n // 2 :], (el, ZAT)),
            (arc[: n // 2 + 1], (er, ZAT)),
        ):
            C3 = fc.P(corner[0], corner[1], wf)
            pts_ = sorted(
                side_pts, key=lambda p: -p[1]
            )  # apex first, down to springing
            for k in range(len(pts_) - 1):  # infill fan
                add_face(
                    "crown_soot", [C3, fc.P(*pts_[k], wf), fc.P(*pts_[k + 1], wf)], fc.N
                )
            add_face("crown_soot", [C3, fc.P(mid, ZAT, wf), fc.P(*apex, wf)], fc.N)
        for s_ in range(n):
            (u0, v0), (u1, v1) = arc[s_], arc[s_ + 1]
            ang = math.pi * (s_ + 0.5) / n
            inward = -(fc.U * math.cos(ang) + Z * math.sin(ang))
            add_face(
                "crown_soot",
                [
                    fc.P(u0, v0, wf),
                    fc.P(u1, v1, wf),
                    fc.P(u1, v1, wb),
                    fc.P(u0, v0, wb),
                ],
                inward,
            )
            ro = 1 + 0.6 / RA
            o0 = (mid + (u0 - mid) * ro, zsp + (v0 - zsp) * ro)
            o1 = (mid + (u1 - mid) * ro, zsp + (v1 - zsp) * ro)
            add_face(
                "crown_wall",
                [
                    fc.P(u0, v0, 0.12),
                    fc.P(u1, v1, 0.12),
                    fc.P(*o1, 0.12),
                    fc.P(*o0, 0.12),
                ],
                fc.N,
            )
            add_face(
                "crown_wall",
                [fc.P(*o0, wf), fc.P(*o1, wf), fc.P(*o1, 0.12), fc.P(*o0, 0.12)],
                -inward,
            )
            add_face(
                "crown_wall",
                [
                    fc.P(u0, v0, wf),
                    fc.P(u1, v1, wf),
                    fc.P(u1, v1, 0.12),
                    fc.P(u0, v0, 0.12),
                ],
                inward,
            )
        fc.box(
            "crown_wall",
            mid - 0.4,
            mid + 0.4,
            zsp + RA - 0.3,
            zsp + RA + 0.9,
            -0.5,
            0.4,
            ch=0.08,
        )  # keystone
tip_piers("crown_wall", ZS + 1.4, ZAT)
tip_band("crown_soot", ZS + 1.4, ZS + SU - 0.45, R - 0.45, faces=("out",))
tip_window("crown_wall", ZS + SU, Z19 - HD)
tip_band("crown_soot", Z19 - HD + 0.35, ZA0 - 0.7, R - 0.45, faces=("out",))
tip_window("crown_wall", ZA0, ZAT - 2.0)
tip_band("crown_wall", ZAT - 2.0, ZAT)

# ------------------------------------------------------------------ cornice + roof
Z_COR0 = ZAT + 4.4
course("crown_soot", 1.4, ZAT, Z_COR0, 0.0)  # sooted frieze
course("cornice", 0.6, ZAT, ZAT + 0.9, 0.1)  # bed moulding
for p, t, nrm in perimeter_walk(footprint(1.4, 40), 1.25, 0.4):  # dentils
    Facade("d", p, t, nrm, 1).box(
        "cornice",
        -0.3,
        0.3,
        ZAT + 1.3,
        ZAT + 2.1,
        -0.1,
        0.55,
        skip=("w-", "v+"),
        ch=0.06,
    )
course("cornice", 2.0, ZAT + 2.1, ZAT + 2.5, 0.08)  # dentil cap
for p, t, nrm in perimeter_walk(
    footprint(0.0, 40), CO["bracket_pitch"], 1.0
):  # modillion brackets
    fr = Facade("b", p, t, nrm, 1)
    fr.box(
        "cornice",
        -0.4,
        0.4,
        ZAT + 3.2,
        Z_COR0,
        1.8,
        CO["projection"] - 0.4,
        skip=("w-", "v+"),
        ch=0.1,
    )
    fr.box(
        "cornice",
        -0.35,
        0.35,
        ZAT + 2.5,
        ZAT + 3.2,
        1.8,
        2.9,
        skip=("w-", "v+"),
        ch=0.1,
    )
course("cornice", 2.2, ZAT + 2.5, Z_COR0, 0.1)  # modillion band
course("cornice", CO["projection"], Z_COR0, ZC - 1.0, 0.15)  # corona
course("cornice", CO["projection"] + 0.45, ZC - 1.0, ZC - 0.4, 0.12)  # cymatium lip
course("cornice", CO["projection"] - 0.4, ZC - 0.4, ZC, 0.08)
course("cornice", 0.3, ZC, ZP, 0.1)  # parapet / roof
ph = clip_left(footprint(-PH["inset"]), (1, PH["max_y"]), (0, PH["max_y"]))
prism("crown_wall", ph, ZP, ZPH, top=False, bottom=False)  # set-back penthouse
phc = clip_left(
    footprint(-PH["inset"] + 0.5), (1, PH["max_y"] + 0.5), (0, PH["max_y"] + 0.5)
)
prism("cornice", phc, ZPH, ZPH + 0.9)
prism("glass", footprint(-1.25), 0, ZC, top=False, bottom=False)  # dark interior core


# ------------------------------------------------------------------ cowcatcher annex at the tip
def tip_line(o):
    """Open polyline around the tip at offset o: Fifth Ave side from Y_ANNEX, arc, Broadway side to Y_ANNEX."""
    pts = [(-o, Y_ANNEX), (-o, CY)]
    for t in range(1, 15):
        a = math.pi - (math.pi - AE) * t / 14
        pts.append((CX + (R + o) * math.cos(a), CY + (R + o) * math.sin(a)))
    pts.append(((CE + o - NE.y * Y_ANNEX) / NE.x, Y_ANNEX))
    return pts


AO = AN["offset"]
AH = AN["height"]
outer, inner = tip_line(AO), tip_line(-0.5)
ann_segments = []
for i in range(len(outer) - 1):
    p, q = Vector((*outer[i], 0)), Vector((*outer[i + 1], 0))
    d = q - p
    nrm = Vector(
        (-d.y, d.x, 0)
    ).normalized()  # polyline runs clockwise around the tip: outward is left
    if nrm.dot(Vector((p.x - CX, p.y - CY, 0)) + Vector((q.x - CX, q.y - CY, 0))) < 0:
        nrm = -nrm
    ann_segments.append(Facade("annex", p, d, nrm, d.length))
door_segs = {0, len(ann_segments) - 1}
for k, fc in enumerate(ann_segments):
    L = fc.L
    fc.box("annex_frame", 0, L, 0, 1.0, -0.6, 0.05, skip=("w-",), ch=0.04)  # bulkhead
    fc.box(
        "annex_frame",
        0,
        L,
        AN["glass_top"],
        AN["glass_top"] + 0.3,
        -0.6,
        0.0,
        skip=("w-",),
    )
    fc.box(
        "signage", 0, L, AN["glass_top"] + 0.3, AH - 0.8, -0.6, 0.12, skip=("w-",)
    )  # sign band
    fc.box(
        "annex_frame", -0.05, L + 0.05, AH - 0.8, AH, -0.6, 0.6, skip=("w-",), ch=0.08
    )  # cornice
    fc.box(
        "annex_frame",
        0,
        L,
        AN["transom"],
        AN["transom"] + 0.22,
        -0.55,
        -0.05,
        skip=("w-",),
    )
    nlit = max(1, round(L / AN["pitch"]))
    door_at = nlit // 2 if k in door_segs and nlit >= 3 else None
    for j in range(nlit):
        a, b = L * j / nlit, L * (j + 1) / nlit
        if j == door_at:
            d = 1.8
            fc.quad("glass", a + 0.1, b - 0.1, 0, AN["transom"], -0.35 - d)
            for uu, nr in ((a + 0.1, fc.U), (b - 0.1, -fc.U)):
                add_face(
                    "glass",
                    [
                        fc.P(uu, 0, -0.35),
                        fc.P(uu, 0, -0.35 - d),
                        fc.P(uu, AN["transom"], -0.35 - d),
                        fc.P(uu, AN["transom"], -0.35),
                    ],
                    nr,
                )
                fc.box(
                    "annex_frame",
                    uu - 0.08,
                    uu + 0.08,
                    0,
                    AN["transom"],
                    -0.45 - d,
                    -0.3 - d,
                    skip=("w-",),
                )
            fc.box(
                "annex_frame",
                a + 0.5,
                b - 0.5,
                3.6,
                3.8,
                -0.3 - d,
                -0.15 - d,
                skip=("w-",),
            )
            add_face(
                "annex_frame",
                [
                    fc.P(a, AN["transom"], -0.35),
                    fc.P(b, AN["transom"], -0.35),
                    fc.P(b, AN["transom"], -0.35 - d),
                    fc.P(a, AN["transom"], -0.35 - d),
                ],
                -Z,
            )
            awning(fc, a - 0.6, b + 0.6, AN["glass_top"] - 0.1, 1.6, 3.2)
        else:
            fc.quad("glass", a, b, 1.0, AN["transom"], -0.35)
        fc.quad("glass", a, b, AN["transom"] + 0.22, AN["glass_top"], -0.35)
        fc.box(
            "mullions",
            a - 0.1,
            a + 0.1,
            0 if j == door_at else 1.0,
            AN["glass_top"],
            -0.55,
            0.0,
            skip=("w-",),
        )
    fc.box("mullions", L - 0.1, L + 0.1, 1.0, AN["glass_top"], -0.55, 0.0, skip=("w-",))
for i in range(len(outer) - 1):  # annex roof
    add_face(
        "annex_frame",
        [(*outer[i], AH), (*outer[i + 1], AH), (*inner[i + 1], AH), (*inner[i], AH)],
        Z,
    )
for end in (0, -1):  # end returns at Y_ANNEX
    p, q = Vector((*outer[end], 0)), Vector((*inner[end], 0))
    d = p - q
    fr = Facade("end", q, d, Vector((0, -1, 0)), d.length)
    fr.box("annex_frame", 0, d.length, 0, AH, -0.4, 0.0, skip=("w-",))

# ------------------------------------------------------------------ sidewalk, curb, trees, lamppost, subway, gum
SW = Fz["sidewalk"]
BIS = (Vector((0, 1, 0)) + east.U).normalized()
TIP = Vector((CX, CY, 0)) + BIS * R
PERP = Vector((BIS.y, -BIS.x, 0))
y_cut = SW["from_y"]
band_poly = clip_left(footprint(SW["width"], 20), (0, y_cut), (1, y_cut))
plaza_far = TIP + BIS * SW["plaza_reach"]
pts = band_poly + [
    tuple((plaza_far + PERP * s_ * SW["plaza_halfwidth"]).to_2d()) for s_ in (-1, 1)
]
walk = ccw(hull(pts))
inner_bld = footprint(-1.5)

# street furniture positions (all framed from the building's own lines)
trees = []
for fc, us in ((east, (0.38, 0.52, 0.66)), (west, (0.5, 0.68))):
    for f_ in us:
        p = fc.P(fc.L * f_, 0, 0) + fc.N * (SW["width"] - 3.2)
        if p.y > y_cut + 4:
            trees.append(p)
trees.append(TIP + BIS * 24 - PERP * 15)
trees.append(TIP + BIS * 24 + PERP * 15)
trees = trees[: DET["trees"] + 2]
subway_c = TIP + BIS * 44 + PERP * 13
SUB_L, SUB_W = 11.0, 4.2


def in_subway(p, pad=0.0):
    d = Vector((p[0], p[1], 0)) - subway_c
    return abs(d.dot(BIS)) < SUB_L / 2 + pad and abs(d.dot(PERP)) < SUB_W / 2 + pad


def in_pit(p, pad=0.0):
    return any(
        abs(p[0] - t.x) < 2.2 + pad and abs(p[1] - t.y) < 2.2 + pad for t in trees
    )


s_ = SW["slab"]
xs, ys = [p[0] for p in walk], [p[1] for p in walk]
nslabs = 0
x = math.floor(min(xs) / s_) * s_
while x < max(xs):
    y = math.floor(min(ys) / s_) * s_
    while y < max(ys):
        cell = [
            (x + 0.05, y + 0.05),
            (x + s_ - 0.05, y + 0.05),
            (x + s_ - 0.05, y + s_ - 0.05),
            (x + 0.05, y + s_ - 0.05),
        ]
        for i in range(len(walk)):
            if len(cell) < 3:
                break
            cell = clip_left(cell, walk[i], walk[(i + 1) % len(walk)])
        if len(cell) >= 3 and area(cell) > 0.25:
            cc = (
                sum(p[0] for p in cell) / len(cell),
                sum(p[1] for p in cell) / len(cell),
            )
            if not inside(inner_bld, cc) and not in_subway(cc, 0.6):
                prism("sidewalk", cell, -SW["curb_drop"], 0.0, bottom=False)
                nslabs += 1
        y += s_
    x += s_
for i in range(len(walk)):  # granite curb
    p, q = walk[i], walk[(i + 1) % len(walk)]
    if abs(p[1] - y_cut) < 0.01 and abs(q[1] - y_cut) < 0.01:
        continue
    d = Vector((q[0] - p[0], q[1] - p[1], 0))
    fr = Facade("curb", (*p, 0), d, (d.y, -d.x, 0), d.length)
    fr.box(
        "curb",
        0,
        d.length,
        -SW["curb_drop"] - 0.2,
        0.04,
        -0.6,
        0.02,
        skip=("w-", "v-"),
        ch=0.08,
    )
# gum spots: tiny dark discs, scattered (more near the annex doors and the subway)
ngum = 0
while ngum < DET["gum_spots"]:
    p = (rng.uniform(min(xs), max(xs)), rng.uniform(min(ys), max(ys)))
    if (
        not inside(walk, p)
        or inside(footprint(AO + 0.3), p)
        or in_subway(p, 0.8)
        or in_pit(p, 0.5)
    ):
        continue
    r = rng.uniform(0.06, 0.16)
    add_face(
        "gum",
        [
            (p[0] + r * math.cos(a), p[1] + r * math.sin(a), 0.012)
            for a in (2 * math.pi * k / 6 + rng.random() for k in range(6))
        ],
        Z,
    )
    ngum += 1
for t in trees:  # tree pits + trees
    fr = Facade("pit", t - Vector((2.2, 2.2, 0)), (1, 0, 0), (0, -1, 0), 4.4)
    add_face(
        "tree_pits",
        [
            t + Vector((-2.2, -2.2, 0.03)),
            t + Vector((2.2, -2.2, 0.03)),
            t + Vector((2.2, 2.2, 0.03)),
            t + Vector((-2.2, 2.2, 0.03)),
        ],
        Z,
    )
    for k in range(4):  # low iron guard rail
        ang = k * math.pi / 2
        dvec = Vector((math.cos(ang), math.sin(ang), 0))
        side = Facade(
            "g",
            t + dvec * 2.2 - Vector((-dvec.y, dvec.x, 0)) * 2.2,
            Vector((-dvec.y, dvec.x, 0)),
            dvec,
            4.4,
        )
        side.box("street_iron", 0, 4.4, 0.0, 0.12, -0.15, 0.0, skip=("w-", "v-"))
        side.box("street_iron", 0, 4.4, 1.35, 1.5, -0.12, 0.0, skip=("w-",))
        side.box("street_iron", 0.0, 0.12, 0.1, 1.35, -0.12, 0.0, skip=("w-",))
    trunk = Facade("t", t, (1, 0, 0), (0, -1, 0), 1)
    trunk.cyl("tree_trunks", 0, 0.03, 7.2, 0, 0.32, 7)
    for z_, r_, ang in ((6.2, 1.1, 0.5), (7.4, 0.8, 2.6), (6.8, 0.9, 4.4)):  # limbs
        dvec = Vector((math.cos(ang), math.sin(ang), 0))
        limb = Facade("l", t + dvec * 0.4, dvec, Vector((-dvec.y, dvec.x, 0)), 1)
        limb.box("tree_trunks", 0, 2.2, z_, z_ + 0.35, -0.15, 0.15, skip=())
    rings = [
        (5.8, 0.6),
        (6.8, 3.9),
        (9.2, 5.2),
        (11.8, 4.5),
        (13.6, 2.0),
    ]  # canopy blob, 10-sided
    nseg = 10
    jit = [[rng.uniform(0.85, 1.15) for _ in range(nseg)] for _ in rings]
    for rr in range(len(rings) - 1):
        (za, ra), (zb, rb) = rings[rr], rings[rr + 1]
        for k in range(nseg):
            a0, a1 = 2 * math.pi * k / nseg, 2 * math.pi * (k + 1) / nseg
            pa = [
                t
                + Vector(
                    (ra * jit[rr][k] * math.cos(a0), ra * jit[rr][k] * math.sin(a0), za)
                ),
                t
                + Vector(
                    (
                        ra * jit[rr][(k + 1) % nseg] * math.cos(a1),
                        ra * jit[rr][(k + 1) % nseg] * math.sin(a1),
                        za,
                    )
                ),
                t
                + Vector(
                    (
                        rb * jit[rr + 1][(k + 1) % nseg] * math.cos(a1),
                        rb * jit[rr + 1][(k + 1) % nseg] * math.sin(a1),
                        zb,
                    )
                ),
                t
                + Vector(
                    (
                        rb * jit[rr + 1][k] * math.cos(a0),
                        rb * jit[rr + 1][k] * math.sin(a0),
                        zb,
                    )
                ),
            ]
            mid_ = (a0 + a1) / 2
            add_face(
                "foliage",
                pa,
                Vector((math.cos(mid_), math.sin(mid_), (ra - rb) / max(0.1, zb - za))),
            )
    add_face(
        "foliage",
        [
            t
            + Vector(
                (
                    2.0 * jit[-1][k] * math.cos(2 * math.pi * k / nseg),
                    2.0 * jit[-1][k] * math.sin(2 * math.pi * k / nseg),
                    13.6,
                )
            )
            for k in range(nseg)
        ],
        Z,
    )
# lamppost (NYC-style pole with an arm and a lantern head), near the tip on the Broadway curb
lamp = TIP + BIS * 8 + PERP * (AO + 10.5)
pole = Facade("pole", lamp, (1, 0, 0), (0, -1, 0), 1)
pole.cyl("street_iron", 0, 0, 1.4, 0, 0.55, 8)
pole.cyl("street_iron", 0, 1.4, 20.0, 0, 0.26, 8)
arm_dir = (-PERP).normalized()
arm = Facade("arm", lamp, arm_dir, Vector((-arm_dir.y, arm_dir.x, 0)), 1)
arm.box("street_iron", -0.2, 4.2, 19.6, 19.95, -0.12, 0.12, skip=())
arm.box("street_iron", 3.3, 4.6, 18.9, 19.6, -0.45, 0.45, skip=(), ch=0.05)
arm.box("glass", 3.45, 4.45, 18.75, 18.9, -0.35, 0.35, skip=())
# subway entrance: green railing on three sides, open end facing the tip, stair down into the dark
sub = Facade(
    "sub", subway_c - BIS * (SUB_L / 2) - PERP * (SUB_W / 2), BIS, -PERP, SUB_L
)
for side_u in (0.0, SUB_W):
    rail = Facade(
        "r",
        subway_c - BIS * (SUB_L / 2) - PERP * (SUB_W / 2) + PERP * side_u,
        BIS,
        -PERP if side_u == 0 else PERP,
        SUB_L,
    )
    rail.box("street_iron", 0, SUB_L, 0, 0.5, -0.1, 0.1, skip=("v-",))
    rail.box("street_iron", 0, SUB_L, 3.1, 3.35, -0.12, 0.12, skip=())
    for k in range(12):
        uu = SUB_L * k / 11
        rail.box(
            "street_iron",
            uu - 0.05,
            uu + 0.05,
            0.5,
            3.1,
            -0.05,
            0.05,
            skip=("v-", "v+"),
        )
    for uu in (0.0, SUB_L):
        rail.cyl("street_iron", uu, 0, 3.9, 0, 0.14, 6)
        rail.box(
            "glass", uu - 0.3, uu + 0.3, 3.9, 4.5, -0.3, 0.3, skip=(), ch=0.12
        )  # globe lamp
back = Facade(
    "rb", subway_c + BIS * (SUB_L / 2) + PERP * (SUB_W / 2), -PERP, BIS, SUB_W
)
back.box("street_iron", 0, SUB_W, 0, 0.5, -0.1, 0.1, skip=("v-",))
back.box("street_iron", 0, SUB_W, 3.1, 3.35, -0.12, 0.12, skip=())
for k in range(10):  # steps down
    z_ = -0.6 - 0.55 * (k + 1)
    u0 = SUB_L * (0.05 + 0.09 * k)
    sub.box(
        "curb",
        u0,
        u0 + 1.1,
        z_ - 0.55,
        z_,
        -SUB_W + 0.05,
        -0.05,
        skip=("w-", "w+"),
        ch=0.0,
    )
for side_w in (0.0, -SUB_W):  # stair well walls
    add_face(
        "ground_soot",
        [
            sub.P(0, 0, side_w),
            sub.P(SUB_L, 0, side_w),
            sub.P(SUB_L, -7, side_w),
            sub.P(0, -7, side_w),
        ],
        -sub.N if side_w == 0 else sub.N,
    )
print(
    f"[flatiron] sidewalk: {nslabs} slabs, {ngum} gum spots, {len(trees)} trees, curb on {len(walk)} edges; "
    f"awnings on {awning_count} bays; annex {len(ann_segments)} segments"
)

# ------------------------------------------------------------------ objects per tag (split by height over budget)
PARTS = []  # (tag, family, obj)
for fam, (V, F) in GEO.items():
    if not F:
        continue
    tris = sum(len(f) - 2 for f in F)
    nchunk = max(1, math.ceil(tris / SPLIT_AT))
    if nchunk > 1:
        F = sorted(F, key=lambda f: sum(V[i][2] for i in f) / len(f))
    chunks, cur, cur_t = [], [], 0
    target = tris / nchunk
    for f in F:
        cur.append(f)
        cur_t += len(f) - 2
        if cur_t >= target and len(chunks) < nchunk - 1:
            chunks.append(cur)
            cur, cur_t = [], 0
    if cur:
        chunks.append(cur)
    for c, faces in enumerate(chunks):
        tag = fam if len(chunks) == 1 else f"{fam}_{c + 1}"
        used = sorted({i for f in faces for i in f})
        remap = {o: n for n, o in enumerate(used)}
        me = bpy.data.meshes.new(f"Flatiron_{tag}")
        me.from_pydata(
            [V[i] for i in used], [], [tuple(remap[i] for i in f) for f in faces]
        )
        me.validate()
        me.update()
        o = bpy.data.objects.new(f"Flatiron_{tag}", me)
        scene.collection.objects.link(o)
        PARTS.append((tag, fam, o))
print(
    f"[flatiron] geometry built in {time.time() - T0:.0f}s; coping {ZPH + 0.9:.1f}, cornice top {ZC:.1f}"
)

meshes = []
for tag, fam, o in PARTS:
    fin = spec["parts"][fam]
    f = style.finishes[fin]
    tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
    tiled = fam in TILED
    me = {
        "obj": o,
        "tag": tag,
        "family": fam,
        "finish": fin,
        "metal": f["type"] == "metal",
        "tris": tris,
        "tiled": tiled,
    }
    meshes.append(me)
total_tris = sum(me["tris"] for me in meshes)
print(
    f"[flatiron] {len(meshes)} meshes, {total_tris} tris total, max {max(me['tris'] for me in meshes)}"
)
for me in meshes:
    flag = "  OVER BUDGET" if me["tris"] > MAX_TRIS else ""
    print(
        f"[flatiron]   {me['tag']}: {me['tris']} tris ({me['finish']}, {'tiled' if me['tiled'] else 'baked'})"
        f"{flag}"
    )
if any(me["tris"] > MAX_TRIS for me in meshes):
    raise SystemExit("a tag is over the triangle budget")

BIG_UNIQUE = {"cornice"}
TB, TS = style.budgets["texture_big"], style.budgets["texture_small"]
SMALL_TILES = {"gum_spots", "tree_pit_soil", "curb_granite", "window_sash"}
if not QUICK:
    # UVs + materials
    for me in meshes:
        o = me["obj"]
        lp.activate(o)
        if me["tiled"]:
            tiling.tile_uvs(o, STUDS)
        else:
            lp.tag_grain(o)
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.006)
            bpy.ops.object.mode_set(mode="OBJECT")
            fn = rfin.make_finish(
                f"{me['tag']}_{me['finish']}_proc",
                style.finishes[me["finish"]],
                style.wear,
                {"W": A, "H": ZPH},
            )
            o.data.materials.clear()
            o.data.materials.append(fn.mat)
            me.update(mat=fn.mat, sockets=fn.sockets, bsdf=fn.bsdf, out=fn.out)
    # one seamless tile per tiled finish (pipeline tiling.bake_tile, cached by hash)
    t_tile = time.time()
    tile_maps = {}
    for fin in sorted({me["finish"] for me in meshes if me["tiled"]}):
        res = TS if fin in SMALL_TILES else TB
        tile_maps[fin] = tiling.bake_tile(
            fin, style.finishes[fin], style.wear, STUDS, res, os.path.join(OUT, "tiles")
        )
        print(f"[flatiron] tile {fin} ({res}px) t={time.time() - t_tile:.0f}s")
    tile_s = time.time() - t_tile
    for me in meshes:
        if me["tiled"]:
            imgs = {}
            for kind, path in tile_maps[me["finish"]].items():
                img = bpy.data.images.load(path, check_existing=True)
                if kind != "color":
                    img.colorspace_settings.name = "Non-Color"
                imgs[kind] = img
            me["baked"] = imgs
    uniq = [me for me in meshes if not me["tiled"]]
    bake_s = lp.bake(
        uniq, os.path.join(OUT, "textures"), lambda tag: TB if tag in BIG_UNIQUE else TS
    )
    print(f"[flatiron] tiles took {tile_s:.0f}s, unique bake took {bake_s:.0f}s")
    lp.swap_to_baked(meshes)
    lp.export_fbx(meshes, os.path.join(OUT, "flatiron.fbx"))


# ------------------------------------------------------------------ preview (not exported)
def plain(name, hexstr, rough=0.9):
    mt = bpy.data.materials.new(name)
    mt.use_nodes = True
    b = mt.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = lp.lin(hexstr)
    b.inputs["Roughness"].default_value = rough
    return mt


def pbox(name, center, size, hexstr, rough=0.9):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    o = bpy.context.active_object
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(plain(name, hexstr, rough))
    return o


pal = style.palette
gz, BIGD = -SW["curb_drop"], 1500.0
hx, hy = SUB_L / 2 + 0.6, SUB_W / 2 + 0.6


def gp(a, b):
    q = subway_c + BIS * a + PERP * b
    return (q.x, q.y, gz)


gverts = [
    gp(-BIGD, -BIGD),
    gp(BIGD, -BIGD),
    gp(BIGD, BIGD),
    gp(-BIGD, BIGD),
    gp(-hx, -hy),
    gp(hx, -hy),
    gp(hx, hy),
    gp(-hx, hy),
]
gfaces = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
gm = bpy.data.meshes.new("Asphalt")
gm.from_pydata(gverts, [], gfaces)
for poly_ in gm.polygons:
    pass
gm.update()
go = bpy.data.objects.new("Asphalt", gm)
scene.collection.objects.link(go)
go.data.materials.append(plain("Asphalt", pal.get("asphalt", "#3A3A3C"), 0.8))
pbox("StairPit", (subway_c.x, subway_c.y, -8), (30, 30, 0.2), "#1A1918")
me_ = bpy.data.meshes.new("SidewalkRest")
poly = ccw(clip_left(footprint(SW["width"]), (1, y_cut + 1), (0, y_cut + 1)))
me_.from_pydata([(x, y, -0.12) for x, y in poly], [], [tuple(range(len(poly)))])
o = bpy.data.objects.new("SidewalkRest", me_)
scene.collection.objects.link(o)
o.data.materials.append(plain("SidewalkRest", pal.get("concrete", "#8E8B85")))
marker_xy = TIP + BIS * 16 - PERP * 6
pbox(
    "Marker", (marker_xy.x, marker_xy.y, 2.75), (2, 1, 5.5), "#808080", 0.6
)  # 2x5.5x1 character marker

# overcast_exterior, as in the other spike previews, with a soft horizon-to-zenith gradient so glass reflects sky
world = bpy.data.worlds.new("World")
world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
bg = wn["Background"]
tc = wn.new("ShaderNodeTexCoord")
sep = wn.new("ShaderNodeSeparateXYZ")
ramp = wn.new("ShaderNodeValToRGB")
wl.new(tc.outputs["Generated"], sep.inputs[0])
mad = wn.new("ShaderNodeMath")
mad.operation = "MULTIPLY_ADD"
mad.inputs[1].default_value = 0.5
mad.inputs[2].default_value = 0.5
wl.new(sep.outputs["Z"], mad.inputs[0])
wl.new(mad.outputs[0], ramp.inputs["Fac"])
ramp.color_ramp.elements[0].position = 0.45
ramp.color_ramp.elements[0].color = (0.36, 0.37, 0.38, 1)
ramp.color_ramp.elements[1].position = 1.0
ramp.color_ramp.elements[1].color = (0.50, 0.56, 0.64, 1)
mid_el = ramp.color_ramp.elements.new(0.52)
mid_el.color = (0.72, 0.74, 0.78, 1)
wl.new(ramp.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 0.95
scene.world = world
bpy.ops.object.light_add(type="SUN", location=(0, 0, 50))
sun = bpy.context.active_object
sun.data.energy = 1.6
sun.data.angle = math.radians(8)
sun.rotation_euler = (math.radians(55), 0, math.radians(-35))

cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.data.clip_end = 5000
cam.data.clip_start = 0.05
scene.collection.objects.link(cam)
target = bpy.data.objects.new("Target", None)
scene.collection.objects.link(target)
c = cam.constraints.new("TRACK_TO")
c.target, c.track_axis, c.up_axis = target, "TRACK_NEGATIVE_Z", "UP_Y"
scene.camera = cam
if QUICK:
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.color_type = "RANDOM"
    scene.display.shading.light = "STUDIO"
else:
    scene.render.engine = "CYCLES"
    lp.use_gpu()
    scene.cycles.use_denoising = True
scene.view_settings.view_transform = (
    "AgX" if not QUICK else scene.view_settings.view_transform
)

# cameras framed from the building's own dimensions
HT = ZPH + 1.0
street_cam = TIP + BIS * (SW["plaza_reach"] - 4) + PERP * 4 + Z * 5.0
pitch = math.radians(41)
street_tgt = street_cam + (-BIS * math.cos(pitch) + Z * math.sin(pitch)) * 100
ctr = Vector((A * 0.33, CY * 0.5, 0))
az = math.atan2(BIS.y, BIS.x) + math.radians(
    28
)  # swing from the tip axis toward Fifth Avenue
wide_dir = Vector((math.cos(az), math.sin(az), 0))
wide_cam = ctr + wide_dir * HT * 1.8 + Z * HT * 0.3
u_sf = east.L - AN["back"] - 30
orn_u = west.L * 0.42
orn_cam = west.P(orn_u, 5.0, 8.0)
opitch = math.radians(43)
orn_tgt = orn_cam + (-west.N * math.cos(opitch) + Z * math.sin(opitch)) * 50
crown_cam = TIP + BIS * 50 + PERP * 14 + Z * (ZAT - 10)
shots = (
    ("preview_street", street_cam, street_tgt, 15, (900, 1400), 160),
    ("preview_wide", wide_cam, ctr + Z * HT * 0.48, 30, (1400, 900), 64),
    (
        "preview_storefront",
        east.P(u_sf, 5.5, 15),
        east.P(u_sf + 14, 7.0, 0),
        22,
        (1400, 900),
        96,
    ),
    ("preview_ornament", orn_cam, orn_tgt, 16, (900, 1400), 160),
    (
        "preview_crown",
        crown_cam,
        Vector((CX, CY, 0)) - BIS * 22 + Z * (ZAT + 1),
        30,
        (1400, 900),
        96,
    ),
)
for name, loc, tgt, lens, (rx, ry), spp in shots:
    scene.render.resolution_x, scene.render.resolution_y = rx, ry
    if not QUICK:
        scene.cycles.samples = spp
    lp.look(cam, target, loc, tgt, lens)
    scene.render.filepath = os.path.join(OUT, f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print(f"[flatiron] rendered {name}")
print(f"[flatiron] done in {time.time() - T0:.0f}s -> {OUT}")
