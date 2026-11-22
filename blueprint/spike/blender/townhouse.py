"""
THROWAWAY SPIKE: spec-driven abandoned two-storey machiya-style townhouse.

  blender -b --factory-startup -P townhouse.py -- <spec.json> <out_dir> [--quick]

--quick: geometry only (join for tri counts, workbench renders, no bake/export).
Coordinates: X along the street frontage, Y depth (street/front at -Y), Z up. 1 unit = 1 stud.
"""
import json
import math
import os
import random
import sys
import time

import bpy
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_pipeline as lp  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
SPEC_PATH, OUT = argv[0], argv[1]
QUICK = "--quick" in argv
os.makedirs(OUT, exist_ok=True)
spec = json.load(open(SPEC_PATH))
H = spec["townhouse"]
DMG = spec.get("damage", {})
rng = random.Random(DMG.get("seed", 1))
T0 = time.time()

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
PARTS = {k: [] for k in spec["parts"]}


def chance(key):
    return rng.random() < DMG.get(key, 0.0)


# ------------------------------------------------------------------ dimensions
W, D = H["width"], H["depth"]
YF, YB = -D / 2, D / 2                      # ground-floor front frame line / back wall
SILL, WAIN = H["sill_height"], H["wainscot_top"]
MID0, MID1 = H["mid_beam"]
TOPW, PLATE = H["wall_top"], H["plate_top"]
P = H["post_size"]
YUF = YF + H["upper_setback"]               # upper-floor front wall centre line
KAMOI = H["kamoi"]


# ------------------------------------------------------------------ primitives
def wbox(tag, center, size, rot=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    o = bpy.context.active_object
    o.scale = size
    if rot is not None:
        o.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = o.modifiers.new("Bevel", "BEVEL")
        mod.width, mod.segments, mod.limit_method = bevel, 1, "ANGLE"
    PARTS[tag].append(o)
    return o


def cyl(tag, center, r1, r2, depth, rot=(0, 0, 0), verts=12):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=depth,
                                    location=center, rotation=rot)
    o = bpy.context.active_object
    PARTS[tag].append(o)
    return o


def mesh_obj(tag, verts, faces):
    me = bpy.data.meshes.new(tag)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    o = bpy.data.objects.new(tag, me)
    scene.collection.objects.link(o)
    lp.activate(o)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    PARTS[tag].append(o)
    return o


def loft(tag, rings):
    """Rings: list of equal-length point loops. Side quads + end caps."""
    k = len(rings[0])
    verts = [v for r in rings for v in r]
    faces = []
    for i in range(len(rings) - 1):
        for a in range(k):
            b = (a + 1) % k
            faces.append((i * k + a, i * k + b, (i + 1) * k + b, (i + 1) * k + a))
    faces.append(tuple(range(k)))
    faces.append(tuple((len(rings) - 1) * k + a for a in range(k)))
    return mesh_obj(tag, verts, faces)


def rotate_about(objs, pivot, euler, move=(0, 0, 0)):
    bpy.context.view_layer.update()
    p = Vector(pivot)
    M = Matrix.Translation(p + Vector(move)) @ Euler(euler).to_matrix().to_4x4() @ Matrix.Translation(-p)
    for o in objs:
        o.matrix_world = M @ o.matrix_world


def strut(tag, A, B, w, h, bevel=0.02):
    """Box from point A to point B, cross-section w (horizontal) x h."""
    A, B = Vector(A), Vector(B)
    d = B - A
    o = wbox(tag, (A + B) / 2, (w, d.length, h), bevel=bevel)
    o.rotation_euler = Vector((0, 1, 0)).rotation_difference(d.normalized()).to_euler()
    return o


class MB:
    """Accumulates many small closed pieces into one mesh (for tiles: thousands of pieces)."""

    def __init__(self):
        self.v, self.f = [], []

    def add(self, verts, faces):
        o = len(self.v)
        self.v += [tuple(v) for v in verts]
        self.f += [tuple(i + o for i in f) for f in faces]


MBS = {}


def mb(tag):
    return MBS.setdefault(tag, MB())


class Facade:
    """Local wall coords: u along the wall, v = world Z, w = outward normal."""

    def __init__(self, name, origin, U, Nrm, length):
        self.name, self.O, self.U, self.N, self.L = name, Vector(origin), Vector(U), Vector(Nrm), length

    def world(self, u, v, w):
        return self.O + self.U * u + Vector((0, 0, v)) + self.N * w

    def size(self, su, sv, sw):
        return Vector((abs(self.U.x) * su + abs(self.N.x) * sw, abs(self.U.y) * su + abs(self.N.y) * sw, sv))

    def box(self, tag, u, v, w, su, sv, sw, tilt=0.0, lean=0.0, bevel=0.0):
        o = wbox(tag, self.world(u, v, w), self.size(su, sv, sw), bevel=bevel)
        if tilt or lean:
            R = Matrix.Rotation(tilt, 3, self.N) @ Matrix.Rotation(lean, 3, self.U)
            o.rotation_euler = R.to_euler()
        return o


# ------------------------------------------------------------------ wall pieces
def siding(fc, u0, u1, v0, v1, w=-0.05, damage=True):
    u = u0
    while u < u1 - 0.1:
        bw = min(0.42, u1 - u)
        if not (damage and chance("missing_boards")):
            top = v1
            if damage and chance("broken_boards"):
                top = v0 + (v1 - v0) * rng.uniform(0.3, 0.8)
            fc.box("siding", u + bw / 2, (v0 + top) / 2, w + rng.uniform(-0.02, 0.02),
                   bw - 0.03, top - v0, 0.12, tilt=rng.uniform(-0.012, 0.012))
        u += bw


def plaster_panel(fc, u0, u1, v0, v1, w=-0.15, t=0.25, hole=None, spall=False):
    if hole is None:
        fc.box("plaster", (u0 + u1) / 2, (v0 + v1) / 2, w, u1 - u0, v1 - v0, t)
        return
    hu0, hu1, hv0, hv1 = hole
    fc.box("plaster", (u0 + u1) / 2, (v0 + hv0) / 2, w, u1 - u0, hv0 - v0, t)
    fc.box("plaster", (u0 + u1) / 2, (hv1 + v1) / 2, w, u1 - u0, v1 - hv1, t)
    fc.box("plaster", (u0 + hu0) / 2, (hv0 + hv1) / 2, w, hu0 - u0, hv1 - hv0, t)
    fc.box("plaster", (hu1 + u1) / 2, (hv0 + hv1) / 2, w, u1 - hu1, hv1 - hv0, t)
    if spall:
        # mud backing + bamboo lath grid exposed where the plaster has fallen off
        fc.box("roof_base", (hu0 + hu1) / 2, (hv0 + hv1) / 2, w - t / 2 + 0.02, hu1 - hu0 + 0.1, hv1 - hv0 + 0.1, 0.06)
        u = hu0 + 0.12
        while u < hu1 - 0.05:
            fc.box("frame", u, (hv0 + hv1) / 2, w - 0.02, 0.05, hv1 - hv0, 0.04)
            u += 0.2
        v = hv0 + 0.15
        while v < hv1 - 0.05:
            fc.box("frame", (hu0 + hu1) / 2, v, w - 0.06, hu1 - hu0, 0.05, 0.04)
            v += 0.26
        # ragged edge: plaster crumbs that break the rectangular outline
        for _ in range(7):
            side = rng.randrange(4)
            s = rng.uniform(0.25, 0.55)
            if side == 0:
                cu, cv = rng.uniform(hu0, hu1), hv0 + s / 3
            elif side == 1:
                cu, cv = rng.uniform(hu0, hu1), hv1 - s / 3
            elif side == 2:
                cu, cv = hu0 + s / 3, rng.uniform(hv0, hv1)
            else:
                cu, cv = hu1 - s / 3, rng.uniform(hv0, hv1)
            fc.box("plaster", cu, cv, w, s, s * rng.uniform(0.6, 1.2), t * 0.9, tilt=rng.uniform(-0.6, 0.6))


def lattice(fc, u0, u1, v0, v1, w=0.0, tag="lattice"):
    fr = 0.18
    fc.box(tag, (u0 + u1) / 2, v0 + fr / 2, w, u1 - u0, fr, 0.26)
    fc.box(tag, (u0 + u1) / 2, v1 - fr / 2, w, u1 - u0, fr, 0.26)
    fc.box(tag, u0 + fr / 2, (v0 + v1) / 2, w, fr, v1 - v0, 0.26)
    fc.box(tag, u1 - fr / 2, (v0 + v1) / 2, w, fr, v1 - v0, 0.26)
    n = max(2, int((u1 - u0 - 2 * fr) / 0.3))
    step = (u1 - u0 - 2 * fr) / n
    a, b = v0 + fr, v1 - fr
    for i in range(1, n):
        u = u0 + fr + i * step
        if chance("broken_lattice"):
            if rng.random() < 0.4:
                continue
            cut = a + (b - a) * rng.uniform(0.2, 0.7)
            fc.box(tag, u, (a + cut) / 2, w, 0.1, cut - a, 0.12, tilt=rng.uniform(-0.15, 0.15))
            continue
        fc.box(tag, u, (a + b) / 2, w, 0.1, b - a, 0.12)
    fc.box(tag, (u0 + u1) / 2, (a + b) / 2, w - 0.08, u1 - u0 - 2 * fr, 0.06, 0.05)


def koshi(fc, u0, u1, v0, v1, w, pitch, pushed=()):
    """Dense vertical shop lattice: heavy rails, square bars, two light ties behind."""
    tag = "lattice"
    fc.box(tag, (u0 + u1) / 2, v1 - 0.1, w, u1 - u0, 0.2, 0.24)
    fc.box(tag, (u0 + u1) / 2, v0 + 0.1, w, u1 - u0, 0.2, 0.24)
    a, b = v0 + 0.2, v1 - 0.2
    n = int(round((u1 - u0) / pitch))
    step = (u1 - u0) / n
    for i in range(1, n):
        u = u0 + i * step
        L = b - a
        if i in pushed:  # kicked in at the bottom, still hanging from the top rail
            lean = rng.uniform(0.07, 0.12)
            fc.box(tag, u, (a + b) / 2, w - 0.5 * L * math.sin(lean), 0.1, L, 0.14, lean=lean,
                   tilt=rng.uniform(-0.03, 0.03))
            continue
        if chance("broken_lattice"):
            if rng.random() < 0.35:
                continue  # bar gone
            cut = rng.uniform(0.3, 0.75)
            if rng.random() < 0.6:  # top part kept, snapped end swings
                fc.box(tag, u, b - L * cut / 2, w, 0.1, L * cut, 0.14, tilt=rng.uniform(-0.08, 0.08))
            else:
                fc.box(tag, u, a + L * cut / 2, w, 0.1, L * cut, 0.14, tilt=rng.uniform(-0.1, 0.1))
            continue
        fc.box(tag, u, (a + b) / 2, w, 0.1, L, 0.14)
    for f in (0.36, 0.7):  # light horizontal ties behind the bars (one snapped)
        if f > 0.5:
            fc.box(tag, (u0 + u1) / 2 - 0.7, a + (b - a) * f, w - 0.11, u1 - u0 - 1.4, 0.06, 0.05)
        else:
            fc.box(tag, (u0 + u1) / 2, a + (b - a) * f, w - 0.11, u1 - u0, 0.06, 0.05)


def door_leaf(fc, u0, u1, v0, v1, w):
    objs = []
    st, t = 0.15, 0.14
    objs.append(fc.box("doors", u0 + st / 2, (v0 + v1) / 2, w, st, v1 - v0, t))
    objs.append(fc.box("doors", u1 - st / 2, (v0 + v1) / 2, w, st, v1 - v0, t))
    objs.append(fc.box("doors", (u0 + u1) / 2, v1 - 0.08, w, u1 - u0, 0.16, t))
    objs.append(fc.box("doors", (u0 + u1) / 2, v0 + 0.11, w, u1 - u0, 0.22, t))
    kick = v0 + 2.2
    objs.append(fc.box("doors", (u0 + u1) / 2, kick, w, u1 - u0, 0.14, t))
    objs.append(fc.box("doors", (u0 + u1) / 2, (v0 + 0.22 + kick) / 2, w - 0.03, u1 - u0 - 2 * st,
                       kick - v0 - 0.22, 0.05))
    n = 7
    step = (u1 - u0 - 2 * st) / n
    a, b = kick + 0.07, v1 - 0.16
    for i in range(1, n):
        u = u0 + st + i * step
        if chance("broken_lattice"):
            if rng.random() < 0.5:
                continue
            cut = rng.uniform(0.3, 0.6)
            objs.append(fc.box("doors", u, b - (b - a) * cut / 2, w, 0.06, (b - a) * cut, 0.08,
                               tilt=rng.uniform(-0.1, 0.1)))
            continue
        objs.append(fc.box("doors", u, (a + b) / 2, w, 0.06, b - a, 0.08))
    for f in (0.33, 0.66):
        objs.append(fc.box("doors", (u0 + u1) / 2, a + (b - a) * f, w - 0.05, u1 - u0 - 2 * st, 0.05, 0.04))
    return objs


# ------------------------------------------------------------------ foundation (single stone course)
def stone_run(a0, a1, fixed, axis, skip=None):
    cur = a0
    while cur < a1 - 0.05:
        ln = min(rng.uniform(1.0, 1.8), a1 - cur)
        mid = cur + ln / 2
        if skip and skip[0] < mid < skip[1]:
            cur += ln
            continue
        push = rng.uniform(0.04, 0.12) if rng.random() < 0.2 else 0.0
        tilt = (rng.uniform(-0.02, 0.02), rng.uniform(-0.02, 0.02), rng.uniform(-0.04, 0.04))
        if axis == "x":
            wbox("foundation", (mid, fixed - push * math.copysign(1, fixed), SILL / 2), (ln - 0.05, 0.7, SILL),
                 rot=tilt, bevel=0.06)
        else:
            wbox("foundation", (fixed + push * math.copysign(1, fixed), mid, SILL / 2), (0.7, ln - 0.05, SILL),
                 rot=tilt, bevel=0.06)
        cur += ln


DB0, DB1 = H["door_bay"]
stone_run(-W / 2 - 0.3, W / 2 + 0.3, YF, "x", skip=(DB0, DB1))
stone_run(-W / 2 - 0.3, W / 2 + 0.3, YB, "x")
stone_run(YF + 0.4, YB - 0.4, -W / 2, "y")
stone_run(YF + 0.4, YB - 0.4, W / 2, "y")
wbox("foundation", ((DB0 + DB1) / 2, YF, 0.13), (DB1 - DB0 + 0.4, 0.75, 0.26), bevel=0.04)    # threshold slab
wbox("foundation", (0, 0, 0.15), (W - 0.8, D - 0.8, 0.3))                                     # doma / floor fill
wbox("foundation", ((DB0 + DB1) / 2 + 0.15, YF - 1.35, 0.12), (2.3, 1.1, 0.24),
     rot=(0, 0.02, 0.06), bevel=0.08)                                                          # step stone

# ------------------------------------------------------------------ front: ground floor (shopfront)
FR = Facade("front", (0, YF, 0), (1, 0, 0), (0, -1, 0), W)
for u in H["front_posts"]:
    FR.box("frame", u, (SILL + MID1) / 2, 0, P, MID1 - SILL, P, bevel=0.03)
FR.box("frame", 0, (MID0 + MID1) / 2, 0.05, W + P, MID1 - MID0, 0.62, bevel=0.03)   # ground-storey beam
FR.box("frame", 0, KAMOI + 0.15, 0.02, W, 0.3, 0.5)                                 # kamoi / door head rail
siding(FR, -W / 2 + P / 2, W / 2 - P / 2, KAMOI + 0.3, MID0, w=-0.12, damage=False)  # head band boards

KB0, KB1 = H["koshi_bay"]
KBASE = H["koshi_base_top"]
siding(FR, KB0, KB1, SILL, KBASE)
FR.box("frame", (KB0 + KB1) / 2, KBASE + 0.1, 0.02, KB1 - KB0, 0.2, 0.42)
koshi(FR, KB0, KB1, KBASE + 0.2, KAMOI, 0.06, H["koshi_pitch"], pushed=set(H["koshi_pushed"]))

# sliding doors: left fixed, right slid half open behind it and off its track
FR.box("frame", (DB0 + DB1) / 2, 0.36, 0.0, DB1 - DB0, 0.2, 0.55)                    # threshold rail
half = (DB1 - DB0) / 2
door_leaf(FR, DB0, DB0 + half, 0.46, KAMOI, 0.02)
shift = half * H["door_open"]
right_leaf = door_leaf(FR, DB0 + half - shift, DB1 - shift, 0.46, KAMOI - 0.05, -0.2)
rotate_about(right_leaf, FR.world(DB1 - shift, 0.46, -0.2), (0.0, 0.035, 0.0), move=(0, 0, 0.02))

BB0, BB1 = H["board_bay"]
siding(FR, BB0, BB1, SILL, KAMOI)

# ------------------------------------------------------------------ front: upper floor
UP = Facade("upper", (0, YUF, 0), (1, 0, 0), (0, -1, 0), W)
MU = H["mushiko"]
MU0, MU1 = MU["u"]
MV0, MV1 = MU["v"]
plaster_panel(UP, -W / 2 + P / 2, W / 2 - P / 2, MID1, TOPW, w=0.0, t=0.4, hole=(MU0, MU1, MV0, MV1))
UP.box("frame", 0, (MID0 + MID1) / 2, -0.05, W, MID1 - MID0, 0.5)
UP.box("frame", 0, (TOPW + PLATE) / 2, 0.05, W + P, PLATE - TOPW, 0.6, bevel=0.03)   # top plate
UP.box("plaster", (MU0 + MU1) / 2, MV0 - 0.09, 0.12, MU1 - MU0 + 0.5, 0.18, 0.62, bevel=0.04)  # sill moulding
UP.box("plaster", (MU0 + MU1) / 2, MV1 + 0.1, 0.12, MU1 - MU0 + 0.5, 0.2, 0.62, bevel=0.04)   # head moulding
nb = int(round((MU1 - MU0) / MU["bar_pitch"]))
bstep = (MU1 - MU0) / nb
for i in range(nb):
    u = MU0 + (i + 0.5) * bstep
    if i in MU["missing"]:  # only a broken stub hangs from the head
        UP.box("plaster", u, MV1 - 0.2, 0.0, 0.3, 0.4, 0.34, bevel=0.08)
        continue
    if i in MU["crumbled"]:  # plaster gone from the lower half: the wooden core shows
        cut = MV0 + (MV1 - MV0) * rng.uniform(0.45, 0.65)
        UP.box("plaster", u, (cut + MV1) / 2, 0.0, 0.3, MV1 - cut, 0.34, bevel=0.08)
        UP.box("frame", u + 0.02, (MV0 + cut) / 2, 0.0, 0.1, cut - MV0, 0.1, tilt=rng.uniform(-0.05, 0.05))
        UP.box("plaster", u, MV0 + 0.1, 0.0, 0.32, 0.2, 0.34, bevel=0.06)  # crumb on the sill
        continue
    UP.box("plaster", u, (MV0 + MV1) / 2, 0.0, 0.3, MV1 - MV0, 0.34, bevel=0.08)

# udatsu: small plastered firewall wings at both ends of the upper floor
UD = H["udatsu"]
for sx in (-1, 1):
    x = sx * UD["x"]
    y0, y1 = UD["y"]
    wbox("plaster", (x, (y0 + y1) / 2, (MID1 + UD["top"]) / 2 - 0.1), (0.5, abs(y1 - y0), UD["top"] - MID1 + 0.2),
         bevel=0.04)
    wbox("frame", (x, (y0 + y1) / 2, UD["top"] + 0.05), (0.6, abs(y1 - y0) + 0.2, 0.12))
    for side in (-1, 1):
        if sx < 0 and side > 0:
            continue  # the left wing has lost half its cap
        wbox("roof_base", (x + side * 0.2, (y0 + y1) / 2, UD["top"] + 0.22), (0.46, abs(y1 - y0) + 0.35, 0.07),
             rot=(0, side * -0.5, 0))
    c = cyl("ridge", (x, (y0 + y1) / 2, UD["top"] + 0.38), 0.12, 0.12, abs(y1 - y0) + 0.4,
            rot=(math.pi / 2, 0, 0), verts=8)
    if sx < 0:
        c.rotation_euler = (math.pi / 2 + 0.06, 0.25, 0)


# ------------------------------------------------------------------ sides + back
def bay_ground(fc, kind, u0, u1):
    if kind == "window":
        s0, s1 = 3.4, 6.4
        siding(fc, u0, u1, SILL + 0.3, s0)
        fc.box("frame", (u0 + u1) / 2, s0, 0.0, u1 - u0, 0.28, 0.5)
        fc.box("frame", (u0 + u1) / 2, s1, 0.0, u1 - u0, 0.28, 0.5)
        lattice(fc, u0 + 0.2, u1 - 0.2, s0 + 0.14, s1 - 0.14)
        plaster_panel(fc, u0, u1, s1 + 0.14, MID0)
        plaster_panel(fc, u0, u0 + 0.2, s0 + 0.14, s1 - 0.14)
        plaster_panel(fc, u1 - 0.2, u1, s0 + 0.14, s1 - 0.14)
    else:
        siding(fc, u0, u1, SILL + 0.3, WAIN)
        fc.box("frame", (u0 + u1) / 2, WAIN, 0.0, u1 - u0, 0.3, 0.48)
        plaster_panel(fc, u0, u1, WAIN + 0.15, MID0)


def bay_upper(fc, kind, u0, u1):
    if kind == "window":
        c = (u0 + u1) / 2
        hole = (c - 1.0, c + 1.0, 10.9, 12.6)
        plaster_panel(fc, u0, u1, MID1, TOPW, hole=hole)
        lattice(fc, hole[0], hole[1], hole[2], hole[3], w=-0.1)
    elif kind == "spall":
        hu0 = u0 + (u1 - u0) * rng.uniform(0.15, 0.3)
        hu1 = u1 - (u1 - u0) * rng.uniform(0.15, 0.3)
        hole = (hu0, hu1, MID1 + 1.1, MID1 + rng.uniform(3.0, 3.8))
        plaster_panel(fc, u0, u1, MID1, TOPW, hole=hole, spall=True)
    else:
        plaster_panel(fc, u0, u1, MID1, TOPW)


def side_facade(fc, ground, upper, front_u):
    """front_u: u coordinate of the ground-floor front frame line on this facade."""
    n = len(ground)
    bw = D / n
    sgn = math.copysign(1, front_u)
    uc = front_u - sgn * (YUF - YF)  # upper-floor front corner
    for i in range(n + 1):
        u = -D / 2 + i * bw
        if abs(u - front_u) < 0.01:
            fc.box("frame", u, (SILL + MID1) / 2, 0.0, P, MID1 - SILL, P, bevel=0.03)
        else:
            fc.box("frame", u, (SILL + TOPW) / 2, 0.0, P, TOPW - SILL, P, bevel=0.03)
    fc.box("frame", uc, (MID1 + TOPW) / 2, 0.0, P, TOPW - MID1, P, bevel=0.03)
    fc.box("frame", 0, SILL + 0.15, 0.05, D + P, 0.3, 0.58)
    fc.box("frame", 0, (MID0 + MID1) / 2, 0.05, D + P, MID1 - MID0, 0.6, bevel=0.03)
    back_u = -front_u
    fc.box("frame", (uc + back_u) / 2, (TOPW + PLATE) / 2, 0.05, abs(back_u - uc) + P, PLATE - TOPW, 0.6,
           bevel=0.03)
    for i in range(n):
        u0 = -D / 2 + i * bw + P / 2
        u1 = -D / 2 + (i + 1) * bw - P / 2
        bay_ground(fc, ground[i], u0, u1)
        uu0, uu1 = u0, u1
        if sgn < 0:
            uu0 = max(u0, uc + P / 2)
        else:
            uu1 = min(u1, uc - P / 2)
        bay_upper(fc, upper[i], uu0, uu1)


SD = H["sides"]
LEFT = Facade("left", (-W / 2, 0, 0), (0, 1, 0), (-1, 0, 0), D)        # u = y
RIGHT = Facade("right", (W / 2, 0, 0), (0, -1, 0), (1, 0, 0), D)      # u = -y
side_facade(LEFT, SD["left_ground"], SD["left_upper"], YF)
side_facade(RIGHT, list(reversed(SD["right_ground"])), list(reversed(SD["right_upper"])), -YF)

BACK = Facade("back", (0, YB, 0), (-1, 0, 0), (0, 1, 0), W)
nbk = len(H["back_ground"])
bwk = W / nbk
for i in range(1, nbk):
    BACK.box("frame", -W / 2 + i * bwk, (SILL + TOPW) / 2, 0.0, P, TOPW - SILL, P, bevel=0.03)
BACK.box("frame", 0, SILL + 0.15, 0.05, W, 0.3, 0.58)
BACK.box("frame", 0, (MID0 + MID1) / 2, 0.05, W + P, MID1 - MID0, 0.6, bevel=0.03)
BACK.box("frame", 0, (TOPW + PLATE) / 2, 0.05, W + P, PLATE - TOPW, 0.6, bevel=0.03)
for i in range(nbk):
    u0 = -W / 2 + i * bwk + P / 2
    u1 = -W / 2 + (i + 1) * bwk - P / 2
    bay_ground(BACK, H["back_ground"][i], u0, u1)
    bay_upper(BACK, H["back_upper"][i], u0, u1)


# ------------------------------------------------------------------ sloped surfaces
class Slope:
    """q = distance down the slope from its top line, off = offset along the slope's up-normal."""

    def __init__(self, y0, z0, side, pitch_deg, L, HX, sag):
        a = math.radians(pitch_deg)
        self.y0, self.z0, self.side, self.c, self.sn = y0, z0, side, math.cos(a), math.sin(a)
        self.L, self.HX, self.sag = L, HX, sag

    def P(self, x, q, off):
        return Vector((x, self.y0 + self.side * (q * self.c + off * self.sn),
                       self.z0 - q * self.sn + off * self.c - self.sag(x, q)))


def slab(tag, S, nx, nq, o0, o1, q0=0.0, q1=None):
    q1 = S.L if q1 is None else q1
    XS = [-S.HX + i * 2 * S.HX / nx for i in range(nx + 1)]
    QS = [q0 + j * (q1 - q0) / nq for j in range(nq + 1)]
    verts, faces = [], []
    n = nq + 1
    for x in XS:
        verts += [S.P(x, q, o1) for q in QS]
        verts += [S.P(x, q, o0) for q in QS]
    st = 2 * n
    for i in range(nx):
        a, b = i * st, (i + 1) * st
        for j in range(nq):
            faces.append((a + j, b + j, b + j + 1, a + j + 1))
            faces.append((a + n + j, a + n + j + 1, b + n + j + 1, b + n + j))
        for j in (0, nq):
            faces.append((a + j, a + n + j, b + n + j, b + j))
    for i in (0, nx):
        a = i * st
        for j in range(nq):
            faces.append((a + j, a + j + 1, a + n + j + 1, a + n + j))
    return mesh_obj(tag, verts, faces)


def along_x(tag, S, q0, q1, o0, o1, nx=16, x0=None, x1=None):
    x0 = -S.HX if x0 is None else x0
    x1 = S.HX if x1 is None else x1
    rings = []
    for i in range(nx + 1):
        x = x0 + i * (x1 - x0) / nx
        rings.append([S.P(x, q0, o0), S.P(x, q1, o0), S.P(x, q1, o1), S.P(x, q0, o1)])
    return loft(tag, rings)


def along_q(tag, S, x, w, q0, q1, o0, o1, nq=4):
    rings = []
    for j in range(nq + 1):
        q = q0 + j * (q1 - q0) / nq
        rings.append([S.P(x - w / 2, q, o0), S.P(x + w / 2, q, o0), S.P(x + w / 2, q, o1), S.P(x - w / 2, q, o1)])
    return loft(tag, rings)


# ------------------------------------------------------------------ hongawara tiles
TL = H["tiles"]
T_LEN, T_COURSE, T_COL = TL["length"], TL["course"], TL["column"]
CONC, (PT0, PT1), RAISE = TL["concavity"], TL["pan_thick"], TL["raise"]
(CR0, CR1), T_OVER, DISC = TL["cover_radius"], TL["eave_overhang"], TL["disc_radius"]
NPAN = 7      # points across a pan arc
NCOV = 7      # points around a cover half-round


def pan(tag, S, xc, wp, q0, q1, yaw=0.0, lift=0.0):
    us = [-wp / 2 + k * wp / (NPAN - 1) for k in range(NPAN)]
    qm = (q0 + q1) / 2
    verts = []
    for q, hb, t in ((q0, 0.0, PT0), (q1, RAISE, PT1)):
        dx = yaw * (q - qm)
        top = [S.P(xc + u + dx, q, lift + hb + CONC * (2 * u / wp) ** 2 + t) for u in us]
        bot = [S.P(xc + u + dx, q, lift + hb + CONC * (2 * u / wp) ** 2) for u in reversed(us)]
        verts += top + bot
    k = 2 * NPAN
    faces = [(a, (a + 1) % k, k + (a + 1) % k, k + a) for a in range(k)]
    for r in (0, k):
        for j in range(NPAN - 1):
            faces.append((r + j, r + j + 1, r + k - 2 - j, r + k - 1 - j))
    mb(tag).add(verts, faces)


def cover(tag, S, xs, q0, q1, yaw=0.0, lift=0.0, disc=False):
    qm = (q0 + q1) / 2
    verts = []
    for q, base, r in ((q0, CONC + PT0 - 0.03, CR0), (q1, RAISE + CONC + PT1 - 0.03, CR1)):
        dx = yaw * (q - qm)
        for k in range(NCOV):
            th = math.pi * k / (NCOV - 1)
            verts.append(S.P(xs + dx + r * math.cos(th), q, lift + base + r * math.sin(th)))
    k = NCOV
    faces = [(a, (a + 1) % k, k + (a + 1) % k, k + a) for a in range(k)]
    faces += [tuple(range(k)), tuple(range(2 * k - 1, k - 1, -1))]
    mb(tag).add(verts, faces)
    if disc:  # round end disc of the eave cover tile
        base = RAISE + CONC + PT1 - 0.03 + lift
        dv = []
        nd = 10
        for q in (q1 - 0.02, q1 + 0.05):
            for j in range(nd):
                th = 2 * math.pi * j / nd
                dv.append(S.P(xs + yaw * (q1 - qm) + DISC * math.cos(th), q, base + 0.04 + DISC * math.sin(th)))
        df = [(a, (a + 1) % nd, nd + (a + 1) % nd, nd + a) for a in range(nd)]
        df += [tuple(range(nd)), tuple(range(2 * nd - 1, nd - 1, -1))]
        mb(tag).add(dv, df)


def tile_slope(tag, S, q_start):
    nc = max(1, round(2 * S.HX / T_COL))
    pc = 2 * S.HX / nc
    tops = []
    qt = S.L + T_OVER - T_LEN
    while qt > q_start + 0.05:
        tops.append(qt)
        qt -= T_COURSE
    tops.append(q_start)
    nk = len(tops)
    holes = DMG.get("roof_holes", {}).get(tag, [])

    def state(i_f, k):
        """i_f: column position (float), k: course index from the eave. -> 'gone' | 'slip' | 'ok'."""
        for hx, hk, hr in holes:
            d = math.hypot(i_f - hx * nc, (k - hk * nk) * 1.1)
            if d < hr:
                return "gone"
            if d < hr + 1.0 and rng.random() < 0.6:
                return "slip"
        if chance("missing_tiles"):
            return "gone"
        if chance("slipped_tiles"):
            return "slip"
        return "ok"

    for k, q0 in enumerate(tops):
        q1 = q0 + T_LEN
        for i in range(nc):
            st = state(i + 0.5, k)
            if st == "gone":
                continue
            slip = rng.uniform(0.25, 0.7) if st == "slip" else 0.0
            yaw = rng.uniform(-0.12, 0.12) if st == "slip" else rng.uniform(-0.012, 0.012)
            lift = (0.05 if st == "slip" else 0.0) + rng.uniform(-0.008, 0.008)
            xc = -S.HX + (i + 0.5) * pc + rng.uniform(-0.015, 0.015)
            pan(tag, S, xc, pc - 0.04, q0 + slip, q1 + slip, yaw, lift)
        for i in range(nc + 1):
            st = state(float(i), k)
            if st == "gone":
                continue
            slip = rng.uniform(0.2, 0.6) if st == "slip" else 0.0
            yaw = rng.uniform(-0.1, 0.1) if st == "slip" else rng.uniform(-0.01, 0.01)
            lift = (0.04 if st == "slip" else 0.0) + rng.uniform(-0.006, 0.006)
            xs = -S.HX + i * pc + rng.uniform(-0.012, 0.012)
            cover(tag, S, xs, q0 + slip, q1 + slip, yaw, lift, disc=(k == 0 and st == "ok"))
    return nc, nk


def flush_tiles():
    for tag, m in MBS.items():
        mesh_obj(tag, m.v, m.f)
    MBS.clear()


# ------------------------------------------------------------------ hisashi (pent roof between floors)
HS = H["hisashi"]
HY0 = YUF - 0.2                      # top line: outer face of the upper wall
HRUN = HY0 - (YF - HS["projection"])
HL = HRUN / math.cos(math.radians(HS["pitch_deg"]))
HHX = W / 2 + HS["overhang_x"]
HSAG, HDROOP = DMG.get("hisashi_sag", 0.0), DMG.get("hisashi_droop", 0.0)


def hisashi_sag(x, q):
    f = max(0.0, q) / HL
    t = max(0.0, 1 - (x / HHX) ** 2)
    return HSAG * t * f + HDROOP * max(0.0, -x / HHX) ** 2 * f ** 1.5


SH = Slope(HY0, HS["z_wall"], -1, HS["pitch_deg"], HL, HHX, hisashi_sag)
slab("roof_base", SH, 16, 4, -0.15, 0.0)
x = -HHX + 0.3
while x < HHX - 0.2:                                                   # exposed rafters
    along_q("frame", SH, x, 0.14, 0.05, HL - 0.08, -0.15, -0.34, nq=4)
    x += 0.55
along_x("eaves", SH, HL - 0.12, HL + 0.03, -0.42, 0.03, nx=16)         # fascia
along_x("frame", SH, HL - 0.8, HL - 0.42, -0.34, -0.74, nx=16)         # dashi-geta outer beam
along_x("ridge", SH, -0.05, 0.55, 0.0, 0.42, nx=16)                    # tile capping against the wall
BEAM_Q = HL - 0.61
for xp in [-W / 2] + H["front_posts"] + [W / 2]:
    B = SH.P(xp, BEAM_Q, -0.74)
    A = Vector((xp, YF - 0.2, B.z - 0.02))
    if xp < -W / 2 + 0.1:  # the left bracket has snapped: a short splintered stub
        stub_end = A + Vector((0, -0.85, -0.22))
        strut("frame", A, stub_end, 0.3, 0.38)
        wbox("frame", (xp - 0.5, YF - 2.4, 0.12), (0.3, 1.6, 0.24), rot=(0, 0, 0.5))  # fallen piece
        continue
    strut("frame", A, B + Vector((0, -0.2, -0.0)), 0.3, 0.4)
tile_slope("tiles_hisashi", SH, 0.35)

# broken tiles fallen onto the street under the drooping end
for i in range(int(DMG.get("fallen_tile_pieces", 0))):
    c = (-W / 2 + rng.uniform(0.2, 3.0), YF - HS["projection"] + rng.uniform(-1.0, 0.9), 0.04)
    wbox("tiles_hisashi", c, (rng.uniform(0.3, 0.6), rng.uniform(0.25, 0.5), 0.07),
         rot=(rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25), rng.uniform(0, math.pi)))
GROUND = Slope(YF - HS["projection"] - 0.3, 0.02, -1, 0.0, 1.2, 1.0, lambda x, q: 0.0)
pan("tiles_hisashi", GROUND, -W / 2 + 1.6, 0.9, 0.0, T_LEN, yaw=0.7)  # one whole pan tile, face up

# ------------------------------------------------------------------ main roof (ridge parallel to the street)
RF = H["roof"]
PITCH = math.radians(RF["pitch_deg"])
HALF = (YB - YUF) / 2
YR = (YB + YUF) / 2
ZR = PLATE + HALF * math.tan(PITCH) + RF["slab"] * math.cos(PITCH)
HX = W / 2 + RF["gable_overhang"]
LF = (HALF + RF["eave_front"]) / math.cos(PITCH)
LB = (HALF + RF["eave_back"]) / math.cos(PITCH)
QW = HALF / math.cos(PITCH)              # q of the wall lines
SAG, EDROOP = DMG.get("roof_sag", 0.0), DMG.get("eave_droop", 0.0)


def roof_sag(front):
    L = LF if front else LB

    def f(x, q):
        t = max(0.0, 1 - (x / HX) ** 2)
        s = SAG * t * (0.4 + 0.6 * (1 - min(1.0, q / L)))
        if front:
            s += EDROOP * max(0.0, x / HX) ** 2 * max(0.0, (q - QW) / (L - QW)) ** 2
        return s
    return f


SRF = Slope(YR, ZR, -1, RF["pitch_deg"], LF, HX, roof_sag(True))
SRB = Slope(YR, ZR, 1, RF["pitch_deg"], LB, HX, roof_sag(False))
for S_ in (SRF, SRB):
    slab("roof_base", S_, 16, 10, -RF["slab"], 0.0)
    along_x("eaves", S_, S_.L - 0.12, S_.L + 0.03, -RF["slab"] - 0.25, 0.03, nx=16)   # fascia
    x = -HX + 0.45
    while x < HX - 0.3:                                                                  # rafter tails
        along_q("eaves", S_, x, 0.2, QW - 0.4, S_.L - 0.1, -RF["slab"], -RF["slab"] - 0.24, nq=3)
        x += 0.9
    for gx in (-1, 1):                                                                   # barge boards
        along_q("eaves", S_, gx * (HX - 0.08), 0.16, 0.0, S_.L + 0.03, -RF["slab"] - 0.3, 0.2, nq=8)
nc_f, nk_f = tile_slope("tiles_front", SRF, 0.45)
nc_b, nk_b = tile_slope("tiles_back", SRB, 0.45)

# ridge: stacked noshi courses + round cap, onigawara at both ends
PROF = [(-0.85, -0.25), (0.85, -0.25), (0.8, 0.12), (0.62, 0.16), (0.6, 0.38), (0.46, 0.42), (0.44, 0.62),
        (-0.44, 0.62), (-0.46, 0.42), (-0.6, 0.38), (-0.62, 0.16), (-0.8, 0.12)]
XR = [-HX - 0.1 + i * (2 * HX + 0.2) / 24 for i in range(25)]


def ridge_base(x):
    return ZR - SRF.sag(x, 0.0)


loft("ridge", [[Vector((x, YR + dy, ridge_base(x) + dz)) for dy, dz in PROF] for x in XR])
loft("ridge", [[Vector((x, YR + 0.27 * math.cos(2 * math.pi * j / 8),
                        ridge_base(x) + 0.72 + 0.27 * math.sin(2 * math.pi * j / 8))) for j in range(8)]
               for x in XR])
for gx in (-1, 1):
    o = wbox("ridge", (gx * (HX + 0.15), YR, ridge_base(gx * HX) + 0.45), (0.38, 1.9, 1.5), bevel=0.1)
    if gx > 0:  # cracked and leaning
        o.rotation_euler = (0.12, 0.1, 0)

# gable infill (plaster) under the barge boards
for gx in (-1, 1):
    x = gx * (W / 2 - 0.1)
    qs_f = [QW - i * QW / 10 for i in range(11)]
    qs_b = [i * QW / 10 for i in range(1, 11)]
    pts = [Vector((x, YUF, TOPW))] + [SRF.P(x, q, -RF["slab"] - 0.02) for q in qs_f] + \
          [SRB.P(x, q, -RF["slab"] - 0.02) for q in qs_b] + [Vector((x, YB, TOPW))]
    n = len(pts)
    vv = [p + Vector((-0.12, 0, 0)) for p in pts] + [p + Vector((0.12, 0, 0)) for p in pts]
    ff = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    ff += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    mesh_obj("plaster", vv, ff)
    gz = PLATE + (ZR - PLATE) * 0.45
    yy = HALF * 0.55
    wbox("frame", (gx * (W / 2 + 0.05), YR, gz), (0.35, 2 * yy, 0.4))           # gable tie beam
    wbox("frame", (gx * (W / 2 + 0.05), YR, (gz + ZR - 0.6) / 2), (0.35, 0.4, ZR - 0.6 - gz))  # king post

# ------------------------------------------------------------------ props
# collapsed bench: right legs gone, seat dropped onto the street
BX0, BY_ = KB0 + 0.6, YF - 1.55
seat_h = 1.45
for dy in (-0.32, 0.32):
    wbox("props", (BX0 + 0.15, BY_ + dy, (seat_h - 0.06) / 2), (0.14, 0.14, seat_h - 0.06))
seat = [wbox("props", (BX0 + 1.6, BY_, seat_h), (3.3, 0.95, 0.12), bevel=0.02),
        wbox("props", (BX0 + 1.6, BY_ - 0.4, seat_h - 0.12), (3.2, 0.08, 0.14)),
        wbox("props", (BX0 + 1.6, BY_ + 0.4, seat_h - 0.12), (3.2, 0.08, 0.14))]
ang = math.asin((seat_h - 0.12) / 3.1)
rotate_about(seat, (BX0 + 0.15, BY_, seat_h - 0.06), (0, ang, 0.04))
wbox("props", (BX0 + 2.4, BY_ - 0.9, 0.07), (0.14, 1.35, 0.14), rot=(0, 0, 0.9))   # fallen leg
wbox("props", (BX0 + 3.05, BY_ + 0.32, 0.35), (0.14, 0.14, 0.7), rot=(0.05, 0.08, 0))  # snapped stub

# rain barrel with rusted hoops and an askew lid
RBX, RBY = (BB0 + BB1) / 2 + 0.1, YF - 1.25
cyl("props", (RBX, RBY, 1.0), 0.68, 0.74, 2.0, verts=16)
for z in (0.35, 1.0, 1.7):
    cyl("hardware", (RBX, RBY, z), 0.75 - 0.03 * (z - 1.0), 0.75 - 0.03 * (z - 1.0), 0.1, verts=16)
for dx in (-0.25, 0.0, 0.25):
    wbox("props", (RBX + dx, RBY + 0.12, 2.06), (0.22, 1.55, 0.06), rot=(0.06, 0.0, 0.35))

# projecting shop sign: blank board, outer hanger broken so it hangs askew
SPX = H["front_posts"][0]
SY0, SY1 = YF - 0.35, YF - 2.0
rod_z = KAMOI + 0.05
wbox("hardware", (SPX, (SY0 + SY1) / 2, rod_z), (0.08, SY0 - SY1, 0.08))
wbox("hardware", (SPX, SY0 + 0.1, rod_z), (0.22, 0.2, 0.22))  # bracket plate on the post
sign = []
BW_, BH_ = 1.35, 2.2
by0 = SY0 - 0.25
btop = rod_z - 0.35
sign.append(wbox("props", (SPX, by0 - BW_ / 2, btop - BH_ / 2), (0.12, BW_, BH_), bevel=0.02))
for dz, h in ((BH_ / 2 - 0.06, 0.12), (-BH_ / 2 + 0.06, 0.12)):
    sign.append(wbox("props", (SPX, by0 - BW_ / 2, btop - BH_ / 2 + dz), (0.2, BW_, h)))
for dy in (0.06, BW_ - 0.06):
    sign.append(wbox("props", (SPX, by0 - dy, btop - BH_ / 2), (0.2, 0.12, BH_)))
sign.append(wbox("hardware", (SPX, by0 - 0.15, (btop + rod_z) / 2), (0.05, 0.05, rod_z - btop)))  # inner hanger
wbox("hardware", (SPX, by0 - BW_ + 0.15, rod_z - 0.12), (0.05, 0.05, 0.2))   # broken outer hanger stub
rotate_about(sign, (SPX, by0 - 0.15, rod_z), (-0.2, 0.0, 0.03))

flush_tiles()
print(f"[townhouse] built {sum(len(v) for v in PARTS.values())} pieces in {time.time() - T0:.0f}s")
print(f"[townhouse] ridge z={ZR:.2f}, front eave z={SRF.P(0, LF, 0).z:.2f}, hisashi eave z={SH.P(0, HL, 0).z:.2f}, "
      f"tiles front {nc_f}x{nk_f}, back {nc_b}x{nk_b}")

# ------------------------------------------------------------------ join, bake, export
meshes = lp.join_parts(PARTS, spec, {"W": W, "H": ZR}, "Townhouse")
total_tris = sum(me["tris"] for me in meshes)
print(f"[townhouse] {len(meshes)} meshes, {total_tris} tris total, max {max(me['tris'] for me in meshes)}")
for me in meshes:
    print(f"[townhouse]   {me['tag']}: {me['tris']} tris, dims {tuple(round(v, 1) for v in me['obj'].dimensions)}")

BIG = {"siding", "plaster", "tiles_front", "tiles_back", "roof_base", "foundation", "frame", "lattice"}
if not QUICK:
    bake_s = lp.bake(meshes, os.path.join(OUT, "textures"), lambda tag: 1024 if tag in BIG else 512)
    print(f"[townhouse] bake took {bake_s:.0f}s")
    lp.swap_to_baked(meshes)
    lp.export_fbx(meshes, os.path.join(OUT, "townhouse.fbx"))


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


bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, 0))
bpy.context.active_object.data.materials.append(plain("Ground", "#4A4636"))
# dark interiors so openings read as depth (ground storey behind the shopfront, upper storey behind the wall)
pbox("InteriorG", (0, (YF + 0.75 + YB - 0.5) / 2, (0.32 + MID0) / 2), (W - 1.0, YB - 0.5 - YF - 0.75, MID0 - 0.32),
     "#0C0A09")
pbox("InteriorU", (0, (YUF + 0.35 + YB - 0.5) / 2, (MID1 + TOPW) / 2), (W - 1.0, YB - 0.5 - YUF - 0.35, TOPW - MID1),
     "#0C0A09")
pbox("Marker", (-W / 2 - 2.6, YF - 3.2, 2.75), (2, 1, 5.5), "#808080", 0.6)  # 2x5.5x1 character marker

world = bpy.data.worlds.new("World")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.62, 0.66, 0.72, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9
scene.world = world
bpy.ops.object.light_add(type="SUN", location=(0, 0, 50))
sun = bpy.context.active_object
sun.data.energy = 1.6
sun.data.angle = math.radians(8)
sun.rotation_euler = (math.radians(55), 0, math.radians(-35))

cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
scene.collection.objects.link(cam)
target = bpy.data.objects.new("Target", None)
scene.collection.objects.link(target)
c = cam.constraints.new("TRACK_TO")
c.target, c.track_axis, c.up_axis = target, "TRACK_NEGATIVE_Z", "UP_Y"
scene.camera = cam
scene.render.resolution_x, scene.render.resolution_y = 1400, 900
if QUICK:
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.color_type = "RANDOM"
    scene.display.shading.light = "STUDIO"
else:
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 64
    scene.cycles.use_denoising = True

# cameras framed from the asset's own layout
ht = ZR + 1.0
front_edge = YF - HS["projection"]
d_wide = max(ht, D) * 2.0
shots = (
    ("preview_wide", (-0.62 * d_wide, -0.78 * d_wide, ht * 1.0), (0.5, 0.0, ht * 0.42), 35),
    ("preview_street", (-2.6, front_edge - 10.0, 5.0), (0.6, YF, 8.0), 20),
    ("preview_shopfront", (KB0 - 2.2, YF - 8.6, 4.4), ((KB0 + DB1) / 2 - 0.3, YF - 0.6, 5.9), 26),
    ("preview_roof", (HX + 5.0, YF - 7.5, ZR + 3.0), (1.5, YF + 4.5, PLATE + 1.5), 32),
)
for name, loc, tgt, lens in shots:
    lp.look(cam, target, loc, tgt, lens)
    scene.render.filepath = os.path.join(OUT, f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print(f"[townhouse] rendered {name}")
print(f"[townhouse] done in {time.time() - T0:.0f}s -> {OUT}")
