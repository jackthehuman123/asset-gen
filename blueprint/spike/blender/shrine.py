"""
THROWAWAY SPIKE: spec-driven abandoned village shrine (torii + path + hokora on a stone plinth).

  blender -b --factory-startup -P shrine.py -- <spec.json> <out_dir> [--quick]

--quick: geometry only (join for tri counts, workbench renders, no bake/export).
Coordinates: X across the lane, Y depth (torii at -Y, hokora at +Y), Z up. 1 unit = 1 stud.
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

argv = sys.argv[sys.argv.index("--") + 1 :]
SPEC_PATH, OUT = argv[0], argv[1]
QUICK = "--quick" in argv
os.makedirs(OUT, exist_ok=True)
spec = json.load(open(SPEC_PATH))
S = spec["shrine"]
DMG = spec.get("damage", {})
rng = random.Random(DMG.get("seed", 1))
T0 = time.time()

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
PARTS = {k: [] for k in spec["parts"]}


def chance(key):
    return rng.random() < DMG.get(key, 0.0)


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
    bpy.ops.mesh.primitive_cone_add(
        vertices=verts,
        radius1=r1,
        radius2=r2,
        depth=depth,
        location=center,
        rotation=rot,
    )
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
    bpy.context.view_layer.update()  # matrix_world must reflect scale/rotation set just before
    p = Vector(pivot)
    M = (
        Matrix.Translation(p + Vector(move))
        @ Euler(euler).to_matrix().to_4x4()
        @ Matrix.Translation(-p)
    )
    for o in objs:
        o.matrix_world = M @ o.matrix_world


def moss(center, r, flat=0.42, tilt=(0.0, 0.0)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1, location=center)
    o = bpy.context.active_object
    for v in o.data.vertices:
        v.co *= rng.uniform(0.9, 1.08)
        v.co.z = max(v.co.z, -0.2)
    o.scale = (r * rng.uniform(0.9, 1.4), r * rng.uniform(0.9, 1.4), r * flat)
    o.rotation_mode = "ZYX"  # spin about local Z first, then tilt onto the slope
    o.rotation_euler = (tilt[0], tilt[1], rng.uniform(0, math.pi))
    PARTS["moss"].append(o)
    return o


# ------------------------------------------------------------------ dimensions
PL = S["plinth"]
PW, PY0, PY1, PH = PL["width"], PL["y0"], PL["y1"], PL["height"]
B = S["body"]
BW, BY0, BY1 = B["width"], B["y0"], B["y1"]
FLOOR = PH + B["stilt"]
TOP = FLOOR + B["wall_height"]
PS = B["post_size"]
VY0 = BY0 - S["veranda_depth"]  # veranda front edge
YC = (BY0 + BY1) / 2
HALF_D = (BY1 - BY0) / 2

# ------------------------------------------------------------------ plinth (dry-stacked stone)
fallen_slot = None
CH = PL["course_height"]
ncourse = int(round(PH / CH))
for k in range(ncourse):
    zc = CH * k + CH / 2
    sides = (
        ("front", (-PW / 2, PW / 2), PY0 + 0.35, "x", -1),
        ("back", (-PW / 2, PW / 2), PY1 - 0.35, "x", 1),
        ("left", (PY0 + 0.7, PY1 - 0.7), -PW / 2 + 0.35, "y", -1),
        ("right", (PY0 + 0.7, PY1 - 0.7), PW / 2 - 0.35, "y", 1),
    )
    for name, (a0, a1), fixed, ax, out in sides:
        a = a0 + (rng.uniform(0.2, 0.6) if k % 2 else 0.0)
        if a > a0:  # small filler at the start
            pass
        cur = a0
        first = True
        while cur < a1 - 0.05:
            ln = min(
                rng.uniform(0.9, 1.5)
                if not (first and k % 2)
                else rng.uniform(0.4, 0.7),
                a1 - cur,
            )
            first = False
            mid = cur + ln / 2
            push = 0.0
            tilt = (
                rng.uniform(-0.015, 0.015),
                rng.uniform(-0.015, 0.015),
                rng.uniform(-0.03, 0.03),
            )
            # the top-front course, right of the steps: one stone has fallen out
            if (
                fallen_slot is None
                and name == "front"
                and k == ncourse - 1
                and mid > 1.8
            ):
                fallen_slot = (mid, ln)
                cur += ln
                continue
            if chance("displaced_stones"):
                push = rng.uniform(0.06, 0.18)
                tilt = (
                    rng.uniform(-0.06, 0.06),
                    rng.uniform(-0.06, 0.06),
                    rng.uniform(-0.08, 0.08),
                )
            if ax == "x":
                c = (mid, fixed + out * push, zc)
                sz = (ln - 0.05, 0.7, CH - 0.03)
            else:
                c = (fixed + out * push, mid, zc)
                sz = (0.7, ln - 0.05, CH - 0.03)
            wbox("plinth", c, sz, rot=tilt, bevel=0.07)
            cur += ln
wbox(
    "plinth",
    (0, (PY0 + PY1) / 2, (PH - 0.04) / 2),
    (PW - 0.6, PY1 - PY0 - 0.6, PH - 0.04),
)  # core fill
if fallen_slot:
    fx, fl = fallen_slot
    wbox(
        "plinth",
        (fx + 0.3, PY0 - 0.75, 0.3),
        (fl - 0.05, 0.7, CH - 0.03),
        rot=(0.25, 0.1, 0.5),
        bevel=0.07,
    )
    wbox(
        "plinth", (fx, PY0 + 0.6, PH - CH - 0.02), (fl - 0.1, 0.5, 0.05)
    )  # darker gap floor

# ------------------------------------------------------------------ steps up to the plinth + flagstone path
ST = S["steps"]
for k in range(ST["count"]):
    top = PH * (k + 1) / ST["count"]
    y0 = PY0 - 0.4 * (ST["count"] - k)
    w = ST["width"] - 0.1 * k
    if k == 0:  # bottom step cracked in two
        for sx, ww in ((-1, w * 0.55), (1, w * 0.45)):
            cx = -w / 2 + ww / 2 if sx < 0 else w / 2 - ww / 2
            wbox(
                "path",
                (cx + sx * 0.03, (y0 + PY0) / 2, top / 2 - (0.03 if sx > 0 else 0)),
                (ww - 0.06, PY0 - y0, top),
                rot=(0, sx * 0.02, rng.uniform(-0.03, 0.03)),
                bevel=0.06,
            )
    else:
        wbox(
            "path",
            (rng.uniform(-0.04, 0.04), (y0 + PY0) / 2, top / 2),
            (w, PY0 - y0, top),
            rot=(0, 0, rng.uniform(-0.02, 0.02)),
            bevel=0.06,
        )
STEP_Y0 = PY0 - 0.4 * ST["count"]

flagstones = []
y = STEP_Y0 - 0.6
while y > S["path_start_y"]:
    for x0 in (-0.58, 0.58):
        if chance("missing_flagstones"):
            continue
        sz = (rng.uniform(0.95, 1.2), rng.uniform(0.85, 1.05), 0.26)
        sunk = chance("sunk_flagstones")
        z = 0.06 if not sunk else -0.02
        rot = (
            rng.uniform(-0.04, 0.04) * (3 if sunk else 1),
            rng.uniform(-0.04, 0.04) * (3 if sunk else 1),
            rng.uniform(-0.25, 0.25),
        )
        c = (x0 + rng.uniform(-0.12, 0.12), y + rng.uniform(-0.08, 0.08), z)
        wbox("path", c, sz, rot=rot, bevel=0.07)
        flagstones.append(c)
    y -= 1.08

# ------------------------------------------------------------------ hokora: stilts, deck, frame
SX = BW / 2
for x in (-SX + 0.15, 0, SX - 0.15):
    for yy in (VY0 + 0.15, BY0, YC, BY1 - 0.1):
        wbox(
            "frame",
            (x, yy, (PH + FLOOR - 0.15) / 2),
            (0.3, 0.3, FLOOR - 0.15 - PH),
            bevel=0.02,
        )
for yy in (VY0 + 0.15, BY0, BY1 - 0.1):
    wbox("frame", (0, yy, FLOOR - 0.3), (BW + 0.2, 0.25, 0.25))  # sleepers
wbox(
    "frame",
    (0, (VY0 + BY1) / 2 + 0.05, FLOOR - 0.08),
    (BW + 0.5, BY1 - VY0 + 0.1, 0.16),
    bevel=0.02,
)  # deck

for x in (-SX, SX):  # corner + door posts
    for yy in (BY0, BY1):
        wbox("frame", (x, yy, (FLOOR + TOP) / 2), (PS, PS, TOP - FLOOR), bevel=0.03)
DOOR_X = 1.05
DOOR_TOP = FLOOR + 2.4
for x in (-DOOR_X, DOOR_X):
    wbox("frame", (x, BY0, (FLOOR + TOP) / 2), (0.28, 0.3, TOP - FLOOR), bevel=0.02)
for yy in (BY0, BY1):  # top plates + head beam
    wbox("frame", (0, yy, TOP - 0.15), (BW + 0.5, 0.32, 0.3), bevel=0.02)
for x in (-SX, SX):
    wbox("frame", (x, YC, TOP - 0.15), (0.32, BY1 - BY0 + 0.4, 0.3), bevel=0.02)
wbox(
    "frame", (0, BY0 - 0.04, DOOR_TOP + 0.1), (BW + 0.2, 0.3, 0.22), bevel=0.02
)  # nageshi
wbox("frame", (0, BY0 - 0.04, FLOOR + 0.06), (BW, 0.3, 0.12))  # threshold


# walls: vertical yakisugi boards
def boards(fixed, a0, a1, z0, z1, along):
    a = a0
    while a < a1 - 0.05:
        bw = min(0.32, a1 - a)
        if not chance("missing_boards"):
            m = a + bw / 2
            c = (m, fixed, (z0 + z1) / 2) if along == "x" else (fixed, m, (z0 + z1) / 2)
            sz = (
                (bw - 0.02, 0.1, z1 - z0) if along == "x" else (0.1, bw - 0.02, z1 - z0)
            )
            wbox("walls", c, sz, rot=(0, 0, rng.uniform(-0.01, 0.01)))
        a += bw


boards(BY1, -SX, SX, FLOOR + 0.1, TOP - 0.3, "x")
for x in (-SX, SX):
    boards(x, BY0, BY1, FLOOR + 0.1, TOP - 0.3, "y")
for a0, a1 in ((-SX, -DOOR_X), (DOOR_X, SX)):
    boards(BY0, a0, a1, FLOOR + 0.1, TOP - 0.3, "x")
boards(BY0, -DOOR_X, DOOR_X, DOOR_TOP + 0.2, TOP - 0.3, "x")


# gable triangles under the roof are built after the roof functions (below)


# lattice doors
def leaf(x0, x1, z0, z1, yy):
    objs = []
    fr = 0.12
    objs.append(wbox("doors", ((x0 + x1) / 2, yy, z0 + fr / 2), (x1 - x0, 0.12, fr)))
    objs.append(wbox("doors", ((x0 + x1) / 2, yy, z1 - fr / 2), (x1 - x0, 0.12, fr)))
    objs.append(wbox("doors", (x0 + fr / 2, yy, (z0 + z1) / 2), (fr, 0.12, z1 - z0)))
    objs.append(wbox("doors", (x1 - fr / 2, yy, (z0 + z1) / 2), (fr, 0.12, z1 - z0)))
    objs.append(
        wbox("doors", ((x0 + x1) / 2, yy, z0 + 0.45), (x1 - x0, 0.1, 0.7))
    )  # kick panel
    n = 5
    for i in range(1, n):
        x = x0 + i * (x1 - x0) / n
        if chance("broken_lattice"):
            if rng.random() < 0.5:
                continue
            cut = rng.uniform(0.3, 0.6)
            objs.append(
                wbox(
                    "doors",
                    (x, yy, z0 + 0.8 + (z1 - z0 - 0.8) * cut / 2),
                    (0.06, 0.07, (z1 - z0 - 0.8) * cut),
                    rot=(0, rng.uniform(-0.15, 0.15), 0),
                )
            )
            continue
        objs.append(
            wbox("doors", (x, yy, (z0 + 0.8 + z1) / 2), (0.06, 0.07, z1 - z0 - 0.8))
        )
    zz = z0 + 0.8
    while zz < z1 - 0.15:
        if not chance("broken_lattice"):
            objs.append(
                wbox(
                    "doors", ((x0 + x1) / 2, yy - 0.02, zz), (x1 - x0 - 0.1, 0.05, 0.05)
                )
            )
        zz += 0.3
    return objs


leaf(-DOOR_X + 0.14, 0.0, FLOOR + 0.12, DOOR_TOP, BY0 - 0.02)
right = leaf(0.0, DOOR_X - 0.14, FLOOR + 0.12, DOOR_TOP, BY0 - 0.02)
if DMG.get("fallen_door"):
    # off its track: slid right, base kicked out, leaning back across the doorway
    rotate_about(
        right, (DOOR_X - 0.14, BY0, FLOOR), (0.16, 0.0, -0.12), move=(0.45, -0.38, 0.0)
    )

# veranda railing
RAIL_Y = VY0 + 0.08
for x in (-SX - 0.05, -1.55, -0.85, 0.85, 1.55, SX + 0.05):
    if abs(x) < SX and chance("missing_rail_posts"):
        continue
    wbox("frame", (x, RAIL_Y, FLOOR + 0.4), (0.12, 0.12, 0.8))
wbox("frame", (-(SX + 0.85) / 2, RAIL_Y, FLOOR + 0.78), (SX - 0.85 + 0.2, 0.12, 0.1))
wbox(
    "frame",
    ((SX + 0.85) / 2 + 0.1, RAIL_Y - 0.05, FLOOR + 0.62),
    (SX - 0.85 + 0.2, 0.12, 0.1),
    rot=(0, 0.22, 0.05),
)  # broken rail, one end dropped
for x in (-SX - 0.05, SX + 0.05):
    wbox("frame", (x, (RAIL_Y + BY0) / 2, FLOOR + 0.78), (0.12, BY0 - RAIL_Y, 0.1))

# stair (kizahashi) from plinth top to deck
N_ST = S["stair_steps"]
SY0, SY1 = PY0 + 0.75, VY0
rise = (FLOOR - PH) / (N_ST + 1)
run = (SY1 - SY0) / N_ST
for k in range(N_ST):
    z = PH + rise * (k + 1)
    wbox(
        "frame",
        (0, SY0 + run * k + run / 2, z - 0.05),
        (1.3, run + 0.08, 0.1),
        bevel=0.01,
    )
slope = math.atan2(FLOOR - PH, SY1 - SY0)
L_str = math.hypot(FLOOR - PH, SY1 - SY0)
for x in (-0.7, 0.7):
    wbox(
        "frame",
        (x, (SY0 + SY1) / 2, (PH + FLOOR) / 2),
        (0.1, L_str + 0.1, 0.3),
        rot=(slope, 0, 0),
    )

# offering box (saisen-bako)
ob = []
OBY = PY0 + 0.38
ob.append(wbox("offering_box", (0, OBY, PH + 0.32), (1.2, 0.55, 0.5), bevel=0.02))
for i in range(5):
    ob.append(
        wbox(
            "offering_box",
            (0, OBY - 0.2 + i * 0.1, PH + 0.62),
            (1.24, 0.06, 0.1),
            rot=(0.5, 0, 0),
        )
    )
for sx in (-1, 1):
    ob.append(wbox("offering_box", (sx * 0.56, OBY, PH + 0.06), (0.1, 0.6, 0.12)))
rotate_about(ob, (0, OBY, PH), (0, 0.03, 0.07))

# ------------------------------------------------------------------ roof
RF = S["roof"]
s0, s1 = (
    math.tan(math.radians(RF["pitch_top_deg"])),
    math.tan(math.radians(RF["pitch_eave_deg"])),
)
LB, LF = HALF_D + RF["eave_back"], HALF_D + RF["eave_front"]
CC = (s0 - s1) / (2 * LB)
T_ = RF["thickness"]
LX = BW + 2 * RF["gable_overhang"]
HX = LX / 2


def drop(h):
    return s0 * h - CC * h * h if h <= LB else (s0 * LB - CC * LB * LB) + s1 * (h - LB)


def dslope(h):
    return s0 - 2 * CC * h if h <= LB else s1


ZR = TOP + drop(HALF_D) + 0.05
SAG, DROOP = DMG.get("roof_sag", 0.0), DMG.get("eave_droop", 0.0)


def sag_at(x, q):
    t = max(0.0, 1 - (2 * x / LX) ** 2)
    L = LF if q < 0 else LB
    w = max(0.0, 1 - abs(q) / L)
    d = SAG * t * (0.4 + 0.6 * w)
    if q < 0 and x < 0:  # front-left eave corner droops
        d += DROOP * (-x / HX) ** 2 * (-q / LF) ** 2
    return d


def RP(x, q, off):
    return Vector((x, YC + q, ZR - drop(abs(q)) - sag_at(x, q) + off))


# profile stations with course steps on top
def side_profile(L):
    dy = RF["course"] * 0.8
    hs = [0.0]
    while hs[-1] + dy < L - 0.1:
        hs.append(hs[-1] + dy)
    hs.append(L)
    pts = []
    for k in range(len(hs) - 1):
        pts.append((hs[k] + 0.01, T_))
        pts.append((hs[k + 1], T_ + 0.07))
    return pts


prof = [(-h, o) for h, o in reversed(side_profile(LF))] + [
    (h, o) for h, o in side_profile(LB)
]
XS = [-HX + i * LX / 16 for i in range(17)]
verts, faces = [], []
nq = len(prof)
for x in XS:
    for q, o in prof:
        verts.append(RP(x, q, o))
    for q, o in prof:
        verts.append(RP(x, q, 0.0))
stride = 2 * nq
for i in range(len(XS) - 1):
    a, b = i * stride, (i + 1) * stride
    for j in range(nq - 1):
        faces.append((a + j, b + j, b + j + 1, a + j + 1))  # top
        faces.append((a + nq + j, a + nq + j + 1, b + nq + j + 1, b + nq + j))  # bottom
    for j in (0, nq - 1):
        faces.append((a + j, a + nq + j, b + nq + j, b + j))  # eave faces
for i in (0, len(XS) - 1):
    a = i * stride
    for j in range(nq - 1):
        faces.append((a + j, a + j + 1, a + nq + j + 1, a + nq + j))  # gable edges
mesh_obj("roof", verts, faces)


def strip_x(tag, q0, q1, o0, o1):
    return loft(
        tag, [[RP(x, q0, o0), RP(x, q1, o0), RP(x, q1, o1), RP(x, q0, o1)] for x in XS]
    )


# layered eave edges (koshi) + rafter tails
for sgn, L in ((-1, LF), (1, LB)):
    strip_x("roof_trim", sgn * (L - 0.06), sgn * (L - 0.55), -0.13, 0.0)
    strip_x("roof_trim", sgn * (L - 0.2), sgn * (L - 0.75), -0.26, -0.13)
    ang = math.atan(dslope(L - 0.8))
    x = -HX + 0.45
    while x < HX - 0.3:
        c = RP(x, sgn * (L - 0.9), -0.36)
        wbox("roof_trim", c, (0.16, 1.3, 0.18), rot=(sgn * -ang, 0, 0))
        x += 0.55
# barge boards along both gable ends
QS = [-LF + i * (LF + LB) / 24 for i in range(25)]
for gx in (-1, 1):
    x = gx * (HX - 0.06)
    loft(
        "roof_trim",
        [
            [
                RP(x - 0.07, q, -0.3),
                RP(x + 0.07, q, -0.3),
                RP(x + 0.07, q, T_ + 0.12),
                RP(x - 0.07, q, T_ + 0.12),
            ]
            for q in QS
        ],
    )

# gable infill triangles (boards behind the barge)
for gx in (-1, 1):
    x = gx * SX
    qs = [-HALF_D + i * (2 * HALF_D) / 12 for i in range(13)]
    loop_o = [Vector((x - gx * 0.0, YC + q, TOP - 0.3)) for q in (-HALF_D, HALF_D)]
    pts = [Vector((x, YC + HALF_D, TOP - 0.3)), Vector((x, YC - HALF_D, TOP - 0.3))]
    pts += [RP(x, q, -0.02) for q in qs]
    n = len(pts)
    vv = [p + Vector((-0.06, 0, 0)) for p in pts] + [
        p + Vector((0.06, 0, 0)) for p in pts
    ]
    ff = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    ff += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    mesh_obj("walls", vv, ff)

# ridge cap
RIDGE_TOP = []
ridge_rings = []
for x in XS:
    z = ZR - sag_at(x, 0) + T_
    ridge_rings.append(
        [
            Vector((x, YC - 0.45, z - 0.75)),
            Vector((x, YC + 0.45, z - 0.75)),
            Vector((x, YC + 0.32, z + 0.28)),
            Vector((x, YC - 0.32, z + 0.28)),
        ]
    )
loft("ridge", ridge_rings)


def ridge_z(x):
    return ZR - sag_at(x, 0) + T_ + 0.28


# katsuogi logs across the ridge
nk = RF["katsuogi"]
fallen_k = False
for i in range(nk):
    x = -HX + 1.0 + i * (LX - 2.0) / (nk - 1)
    if chance("missing_katsuogi"):
        if not fallen_k:  # one lies on the plinth
            cyl(
                "roof_trim",
                (PW / 2 - 1.0, PY1 - 0.7, PH + 0.2),
                0.2,
                0.17,
                1.5,
                rot=(math.pi / 2, 0, 1.1),
                verts=10,
            )
            fallen_k = True
        continue
    cyl(
        "roof_trim",
        (x, YC, ridge_z(x) + 0.18),
        0.2,
        0.2,
        1.5,
        rot=(math.pi / 2, 0, rng.uniform(-0.05, 0.05)),
        verts=10,
    )

# chigi: crossed boards at both gable ends
RISE = RF["chigi_rise"]
for gx in (-1, 1):
    x = gx * (HX - 0.06)
    for sgn in (-1, 1):
        A = RP(x, sgn * 1.9, T_ + 0.12)
        R = Vector((x, YC, ZR - sag_at(x, 0) + T_ + 0.12))
        d = (R - A).normalized()
        Ltot = (R - A).length + RISE / max(d.z, 0.3)
        snapped = gx > 0 and sgn < 0
        if snapped:
            Ltot = (R - A).length + 0.25
        c = A + d * (Ltot / 2)
        rot = Vector((0, 1, 0)).rotation_difference(d).to_euler()
        o = wbox(
            "roof_trim",
            c + Vector((sgn * 0.08, 0, 0)),
            (0.14, Ltot, 0.42),
            rot=rot,
            bevel=0.02,
        )
        if snapped:  # the broken-off tip lies on the back slope
            tip = RP(x - 0.9, 1.3, T_ + 0.15)
            wbox(
                "roof_trim",
                tip,
                (0.14, 1.1, 0.4),
                rot=(-math.atan(dslope(1.3)), 0.25, 0.6),
            )

# ------------------------------------------------------------------ torii
TR = S["torii"]
TY, SPAN, PR = TR["y"], TR["post_span"], TR["post_radius"]
KZ, KL, UP = TR["kasagi_z"], TR["kasagi_length"], TR["kasagi_upturn"]
SHZ = KZ - 0.42  # shimaki underside
for sx in (-1, 1):
    x = sx * SPAN / 2
    cyl("statuary", (x, TY, 0.2), 0.8, 0.62, 0.5, verts=16)
    cyl("torii", (x, TY, (0.4 + SHZ) / 2), PR, PR * 0.86, SHZ - 0.4, verts=20)
    cyl("torii", (x, TY, 0.62), PR + 0.05, PR + 0.05, 0.22, verts=20)  # base band
NZ = TR["nuki_z"]
wbox(
    "torii", (-0.2, TY, NZ), (SPAN + 1.2 - 0.4, 0.34, 0.55), bevel=0.02
)  # right end snapped short
for sx in (-1, 1):
    wbox("torii", (sx * (SPAN / 2 + PR + 0.08), TY, NZ), (0.14, 0.42, 0.42))  # wedges
wbox(
    "torii", (0, TY, (NZ + 0.275 + SHZ) / 2), (0.42, 0.3, SHZ - NZ - 0.275)
)  # gakuzuka
wbox(
    "torii",
    (0.05, TY - 0.2, (NZ + SHZ) / 2 + 0.15),
    (0.8, 0.08, 1.05),
    rot=(0.08, 0.09, 0),
    bevel=0.02,
)  # blank plaque


def beam_rings(L, z0, h, w_bot, w_top, up):
    rings = []
    for i in range(25):
        x = -L / 2 + i * L / 24
        zz = z0 + up * abs(2 * x / L) ** 2.5
        rings.append(
            [
                Vector((x, TY - w_bot, zz)),
                Vector((x, TY + w_bot, zz)),
                Vector((x, TY + w_top, zz + h)),
                Vector((x, TY - w_top, zz + h)),
            ]
        )
    return rings


top_beams = [
    loft("torii", beam_rings(KL - 0.8, SHZ, 0.42, 0.3, 0.3, UP * 0.6)),
    loft("torii", beam_rings(KL, KZ, 0.62, 0.42, 0.34, UP)),
]
rotate_about(
    top_beams,
    (0, TY, KZ),
    (math.radians(0.8), 0, math.radians(DMG.get("torii_kasagi_twist_deg", 0))),
)

# shimenawa: two twisted strands, snapped on the right
RZ, RSAG, RX = NZ - 0.45, 1.0, SPAN / 2 - PR + 0.05


def rope_z(x):
    return RZ - RSAG * (1 - (x / RX) ** 2)


def rope_path(pts_xz_list):
    return [Vector((x, TY, z)) for x, z in pts_xz_list]


def rope(path, rad):
    arc = 0.0
    for strand in range(2):
        cu = bpy.data.curves.new("rope", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = 1.0
        cu.bevel_resolution = 1
        cu.use_fill_caps = True
        sp = cu.splines.new("POLY")
        sp.points.add(len(path) - 1)
        arc = 0.0
        for i, p in enumerate(path):
            if i:
                arc += (path[i] - path[i - 1]).length
            tng = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
            n1 = Vector((0, 1, 0))
            n2 = tng.cross(n1).normalized()
            r = rad(i / (len(path) - 1))
            ph = arc / 0.55 * 2 * math.pi + strand * math.pi
            off = (n1 * math.cos(ph) + n2 * math.sin(ph)) * r * 0.5
            sp.points[i].co = (*(p + off), 1.0)
            sp.points[i].radius = r * 0.62
        o = bpy.data.objects.new("rope", cu)
        scene.collection.objects.link(o)
        lp.activate(o)
        bpy.ops.object.convert(target="MESH")
        PARTS["rope"].append(bpy.context.active_object)


BREAK = 1.4 if DMG.get("snapped_rope") else RX
main = [
    (-RX + i * (BREAK + RX) / 40, rope_z(-RX + i * (BREAK + RX) / 40))
    for i in range(41)
]
zb = rope_z(BREAK)
main += [(BREAK + 0.05 * i, zb - 0.22 * i) for i in range(1, 8)]
rope(rope_path(main), lambda t: 0.1 + 0.08 * math.sin(math.pi * min(t * 1.2, 1.0)))
if DMG.get("snapped_rope"):
    stub = [(RX - i * 0.08, rope_z(RX - i * 0.08)) for i in range(8)]
    stub += [(stub[-1][0] - 0.04 * i, stub[-1][1] - 0.2 * i) for i in range(1, 5)]
    rope(rope_path(stub), lambda t: 0.1)
# shide: zigzag paper streamers
for xs in (-2.2, -0.8, 0.6, 2.9):
    if xs > BREAK and xs < RX - 0.6:
        continue
    if chance("missing_shide"):
        continue
    ztop = rope_z(xs) - 0.12
    n = rng.choice((2, 3, 4))
    for i in range(n):
        wbox(
            "shide",
            (xs + (0.09 if i % 2 else -0.09), TY - 0.02, ztop - 0.17 - 0.3 * i),
            (0.26, 0.02, 0.3),
            rot=(
                rng.uniform(-0.1, 0.1),
                rng.uniform(-0.12, 0.12),
                rng.uniform(-0.3, 0.3),
            ),
        )


# ------------------------------------------------------------------ stone lanterns + guardian blocks
def lantern(x, y, capless):
    k = 1.2
    cyl("statuary", (x, y, 0.15 * k), 0.55 * k, 0.5 * k, 0.3 * k, verts=6)
    cyl("statuary", (x, y, 0.95 * k), 0.2 * k, 0.17 * k, 1.3 * k, verts=8)
    cyl("statuary", (x, y, 1.71 * k), 0.45 * k, 0.6 * k, 0.22 * k, verts=6)
    for dx in (-0.25, 0.25):
        for dy in (-0.25, 0.25):
            wbox(
                "statuary",
                (x + dx * k, y + dy * k, 2.12 * k),
                (0.12 * k, 0.12 * k, 0.6 * k),
            )
    wbox("statuary", (x, y, 1.86 * k), (0.62 * k, 0.62 * k, 0.06 * k))
    wbox("statuary", (x, y, 2.44 * k), (0.72 * k, 0.72 * k, 0.06 * k))
    cap = [
        cyl("statuary", (x, y, 2.72 * k), 0.85 * k, 0.12 * k, 0.5 * k, verts=6),
        cyl("statuary", (x, y, 2.5 * k), 0.85 * k, 0.85 * k, 0.1 * k, verts=6),
    ]
    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=1, radius=0.15 * k, location=(x, y, 3.05 * k)
    )
    PARTS["statuary"].append(bpy.context.active_object)
    cap.append(bpy.context.active_object)
    if capless:  # cap fell into the grass beside the lantern
        rotate_about(
            cap,
            (x, y, 2.7 * k),
            (1.25, 0.2, 0.4),
            move=(-0.75 * math.copysign(1, x), 0.8, -2.25 * k),
        )
        moss((x, y, 2.48 * k), 0.3, 0.5)
    else:
        moss((x + 0.2, y - 0.1, 2.95 * k), 0.35, 0.4)
    moss((x, y, 2.06 * k), 0.4, 0.3)
    moss((x + 0.25, y + 0.1, 0.36 * k), 0.4, 0.35)


def guardian(x, y, toppled):
    wbox("statuary", (x, y, 0.4), (0.95, 1.15, 0.8), bevel=0.06)
    body = [
        wbox("statuary", (x, y + 0.05, 1.2), (0.72, 0.95, 0.8), bevel=0.18),
        wbox("statuary", (x, y - 0.3, 1.8), (0.55, 0.5, 0.5), bevel=0.12),
    ]
    if toppled:
        rotate_about(
            body,
            (x, y, 1.2),
            (0.15, 1.45 * math.copysign(1, x), 0.3),
            move=(0.95 * math.copysign(1, x), 0.1, -0.85),
        )
        moss((x, y, 0.82), 0.45, 0.3)
    else:
        moss((x + 0.1, y + 0.15, 1.62), 0.35, 0.35)


LX_, LY_ = S["lanterns_x"], S["lanterns_y"]
lantern(-LX_, LY_, DMG.get("fallen_lantern_cap", False))
lantern(LX_, LY_, False)
GX, GY = S["guardians_x"], S["guardians_y"]
guardian(-GX, GY, False)
guardian(GX, GY, DMG.get("toppled_guardian", False))

# ------------------------------------------------------------------ moss cushions (geometry)
nm = DMG.get("moss_clumps", 120)
# roof: clusters, heavier toward the eaves and on the front slope
for _ in range(int(nm * 0.45)):
    sgn = -1 if rng.random() < 0.6 else 1
    L = LF if sgn < 0 else LB
    h = L * (1 - rng.random() ** 1.6) * 0.95 + 0.1
    x = rng.uniform(-HX + 0.3, HX - 0.3)
    q = sgn * min(h, L - 0.15)
    ang = math.atan(dslope(abs(q)))
    moss(RP(x, q, T_ + 0.02), rng.uniform(0.3, 0.6), 0.22, tilt=(-sgn * ang, 0))
# ridge + chigi bases
for _ in range(6):
    x = rng.uniform(-HX + 0.5, HX - 0.5)
    moss(
        (x, YC + rng.uniform(-0.3, 0.3), ridge_z(x) - 0.05),
        rng.uniform(0.25, 0.4),
        0.35,
    )
# plinth: top edges + base
for _ in range(int(nm * 0.16)):
    side = rng.random()
    if side < 0.5:
        x, yy = (
            rng.uniform(-PW / 2 + 0.3, PW / 2 - 0.3),
            rng.choice((PY0 + 0.25, PY1 - 0.25)),
        )
    else:
        x, yy = (
            rng.choice((-PW / 2 + 0.25, PW / 2 - 0.25)),
            rng.uniform(PY0 + 0.3, PY1 - 0.3),
        )
    moss((x, yy, PH - 0.02), rng.uniform(0.25, 0.5), 0.35)
for _ in range(int(nm * 0.1)):
    if rng.random() < 0.5:
        x, yy = rng.uniform(-PW / 2, PW / 2), rng.choice((PY0 - 0.05, PY1 + 0.05))
    else:
        x, yy = rng.choice((-PW / 2 - 0.05, PW / 2 + 0.05)), rng.uniform(PY0, PY1)
    moss((x, yy, 0.0), rng.uniform(0.35, 0.6), 0.5)
# steps
for k in range(ST["count"]):
    top = PH * (k + 1) / ST["count"]
    for _ in range(2):
        moss(
            (
                rng.choice((-1, 1)) * rng.uniform(0.6, 1.2),
                PY0 - 0.4 * (ST["count"] - k) + 0.15,
                top - 0.02,
            ),
            rng.uniform(0.2, 0.35),
            0.35,
        )
# path: between and around flagstones
for c in rng.sample(flagstones, min(len(flagstones), int(nm * 0.1))):
    moss(
        (c[0] + rng.choice((-1, 1)) * 0.55, c[1] + rng.uniform(-0.4, 0.4), 0.0),
        rng.uniform(0.25, 0.45),
        0.4,
    )
# torii: kasagi top, base stones
kas = []
for x in (-3.9, -1.2, 2.4):
    kas.append(
        moss(
            (x, TY, KZ + 0.62 + UP * abs(2 * x / KL) ** 2.5 - 0.02),
            rng.uniform(0.16, 0.22),
            0.3,
        )
    )
rotate_about(
    kas,
    (0, TY, KZ),
    (math.radians(0.8), 0, math.radians(DMG.get("torii_kasagi_twist_deg", 0))),
)
for sx in (-1, 1):
    moss((sx * SPAN / 2 + 0.45, TY - 0.3, 0.42), 0.3, 0.4)
    moss((sx * SPAN / 2 - 0.4, TY + 0.4, 0.1), 0.4, 0.45)

print(
    f"[shrine] built {sum(len(v) for v in PARTS.values())} pieces in {time.time() - T0:.0f}s"
)
print(
    f"[shrine] ridge z={ZR + T_:.2f}, torii top ~{KZ + 0.62 + UP:.2f}, front eave z={RP(0, -LF, 0).z:.2f}"
)

# ------------------------------------------------------------------ join, bake, export
meshes = lp.join_parts(PARTS, spec, {"W": PW, "H": KZ}, "Shrine")
total_tris = sum(me["tris"] for me in meshes)
print(f"[shrine] {len(meshes)} meshes, {total_tris} tris total")
mn = Vector((1e9, 1e9, 1e9))
mx = -mn
for me in meshes:
    for c in me["obj"].bound_box:
        w = me["obj"].matrix_world @ Vector(c)
        mn = Vector(map(min, mn, w))
        mx = Vector(map(max, mx, w))
    print(f"[shrine]   {me['tag']}: {tuple(round(v, 1) for v in me['obj'].dimensions)}")
print(
    f"[shrine] bounds (AABB of rotated joined meshes, loose) min={tuple(round(v, 2) for v in mn)} max={tuple(round(v, 2) for v in mx)}"
)

BIG = {"plinth", "path", "roof", "torii", "frame", "walls", "moss", "statuary"}
if not QUICK:
    bake_s = lp.bake(
        meshes, os.path.join(OUT, "textures"), lambda tag: 1024 if tag in BIG else 512
    )
    print(f"[shrine] bake took {bake_s:.0f}s")
    lp.swap_to_baked(meshes)
    lp.export_fbx(meshes, os.path.join(OUT, "shrine.fbx"))


# ------------------------------------------------------------------ preview (not exported)
def plain(name, hexstr, rough=0.9):
    mt = bpy.data.materials.new(name)
    mt.use_nodes = True
    b = mt.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = lp.lin(hexstr)
    b.inputs["Roughness"].default_value = rough
    return mt


bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, 0))
bpy.context.active_object.data.materials.append(plain("Ground", "#4A4636"))
bpy.ops.mesh.primitive_cube_add(
    size=1, location=(0, YC + 0.1, (FLOOR + TOP) / 2)
)  # dark interior
inner = bpy.context.active_object
inner.scale = (BW - 0.4, BY1 - BY0 - 0.4, TOP - FLOOR - 0.2)
bpy.ops.object.transform_apply(scale=True)
inner.data.materials.append(plain("Interior", "#0C0A09"))
bpy.ops.mesh.primitive_cube_add(
    size=1, location=(6.8, -3.0, 2.75)
)  # 2x5.5x1 character marker
mk = bpy.context.active_object
mk.scale = (2, 1, 5.5)
bpy.ops.object.transform_apply(scale=True)
mk.data.materials.append(plain("Marker", "#808080", 0.6))

world = bpy.data.worlds.new("World")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (
    0.62,
    0.66,
    0.72,
    1,
)
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

# cameras framed from the asset's own bounds
# (layout-derived rather than mesh bounds, so a stray piece can't throw the framing off)
ctr = Vector((0, (TY - 0.8 + YC + LB) / 2, 0))
ht = KZ + 0.62 + UP
dep = (YC + LB) - (TY - 0.8)
d_wide = max(ht, dep) * 2.3
shots = (
    (
        "preview_wide",
        (ctr.x - 0.62 * d_wide, ctr.y - 0.7 * d_wide, ht * 1.05),
        (ctr.x + 1.0, ctr.y, ht * 0.4),
        35,
    ),
    (
        "preview_approach",
        (0.7, mn.y - 0.9 * dep, 5.0),
        (0, (PY0 + PY1) / 2, ht * 0.5),
        24,
    ),
    (
        "preview_hokora",
        (-SX - 4.5, VY0 - 4.8, FLOOR + 2.6),
        (0, YC - 0.3, (PH + ZR) / 2),
        35,
    ),
    ("preview_roof", (SX + 5.5, VY0 - 4.0, ZR + 4.5), (0, YC, ZR - 1.2), 35),
)
for name, loc, tgt, lens in shots:
    lp.look(cam, target, loc, tgt, lens)
    scene.render.filepath = os.path.join(OUT, f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print(f"[shrine] rendered {name}")
print(f"[shrine] done in {time.time() - T0:.0f}s -> {OUT}")
