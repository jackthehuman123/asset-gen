"""
THROWAWAY SPIKE: spec-driven Japanese house exterior.

  blender -b --factory-startup -P house.py -- <spec.json> <out_dir>

Coordinates: X along the front, Y depth (front at -Y), Z up. 1 unit = 1 stud.
"""

import json
import math
import os
import random
import sys
import time

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_pipeline as lp  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1 :]
SPEC_PATH, OUT = argv[0], argv[1]
os.makedirs(OUT, exist_ok=True)
spec = json.load(open(SPEC_PATH))
H_ = spec["house"]
DMG = spec.get("damage", {})
rng = random.Random(DMG.get("seed", 1))
T0 = time.time()

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

W, D = H_["width"], H_["depth"]
PLINTH, F = H_["plinth_height"], H_["floor_height"]
WH, WAIN = H_["wall_height"], H_["wainscot_height"]
P = H_["post_size"]
PITCH = math.radians(H_["roof_pitch_deg"])
EAVE, GOV = H_["eave_overhang"], H_["gable_overhang"]
TOP = F + WH
R = (D / 2) * math.tan(PITCH)
ZR = TOP + R  # ridge line (top of wall plane extended)

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


class Facade:
    """Local wall coords: u along the wall, v = world Z, w = outward normal."""

    def __init__(self, name, origin, U, Nrm, length):
        self.name, self.O, self.U, self.N, self.L = (
            name,
            Vector(origin),
            Vector(U),
            Vector(Nrm),
            length,
        )

    def world(self, u, v, w):
        return self.O + self.U * u + Vector((0, 0, v)) + self.N * w

    def size(self, su, sv, sw):
        return Vector(
            (
                abs(self.U.x) * su + abs(self.N.x) * sw,
                abs(self.U.y) * su + abs(self.N.y) * sw,
                sv,
            )
        )

    def box(self, tag, u, v, w, su, sv, sw, tilt=0.0, bevel=0.0):
        o = wbox(tag, self.world(u, v, w), self.size(su, sv, sw), bevel=bevel)
        if tilt:
            o.rotation_mode = "AXIS_ANGLE"
            o.rotation_axis_angle = (tilt, self.N.x, self.N.y, self.N.z)
        return o


# ------------------------------------------------------------------ walls
def siding(fc, u0, u1, v0, v1):
    u = u0
    while u < u1 - 0.1:
        bw = min(0.45, u1 - u)
        if not chance("missing_boards"):
            top = v1
            if chance("broken_boards"):
                top = v0 + (v1 - v0) * rng.uniform(0.3, 0.8)
            fc.box(
                "siding",
                u + bw / 2,
                (v0 + top) / 2,
                -0.05 + rng.uniform(-0.02, 0.02),
                bw - 0.03,
                top - v0,
                0.12,
                tilt=rng.uniform(-0.01, 0.01),
            )
        u += bw


def plaster(fc, u0, u1, v0, v1):
    fc.box("plaster", (u0 + u1) / 2, (v0 + v1) / 2, -0.15, u1 - u0, v1 - v0, 0.25)


def lattice(fc, u0, u1, v0, v1, w=0.0, tag="lattice", break_ok=True):
    fr = 0.22
    fc.box(tag, (u0 + u1) / 2, v0 + fr / 2, w, u1 - u0, fr, 0.3)
    fc.box(tag, (u0 + u1) / 2, v1 - fr / 2, w, u1 - u0, fr, 0.3)
    fc.box(tag, u0 + fr / 2, (v0 + v1) / 2, w, fr, v1 - v0, 0.3)
    fc.box(tag, u1 - fr / 2, (v0 + v1) / 2, w, fr, v1 - v0, 0.3)
    n = max(2, int((u1 - u0 - 2 * fr) / 0.4))
    step = (u1 - u0 - 2 * fr) / n
    a, b = v0 + fr, v1 - fr
    for i in range(1, n):
        u = u0 + fr + i * step
        if break_ok and chance("broken_lattice"):
            if rng.random() < 0.4:
                continue  # bar gone
            cut = a + (b - a) * rng.uniform(0.2, 0.7)  # snapped: keep one end, angled
            if rng.random() < 0.5:
                fc.box(
                    tag,
                    u,
                    (a + cut) / 2,
                    w,
                    0.14,
                    cut - a,
                    0.14,
                    tilt=rng.uniform(-0.15, 0.15),
                )
            else:
                fc.box(
                    tag,
                    u,
                    (cut + b) / 2,
                    w,
                    0.14,
                    b - cut,
                    0.14,
                    tilt=rng.uniform(-0.15, 0.15),
                )
            continue
        fc.box(tag, u, (a + b) / 2, w, 0.14, b - a, 0.14)


def door_panel(fc, u0, u1, v0, v1, w):
    fr = 0.25
    split = v0 + (v1 - v0) * 0.38
    fc.box(
        "doors", (u0 + u1) / 2, (v0 + split) / 2, w, u1 - u0 - 0.1, split - v0, 0.18
    )  # lower solid panel
    lattice(fc, u0, u1, split - fr, v1, w=w, tag="doors")


def bay(fc, kind, idx, u0, u1):
    v_f = F
    boarded = [fc.name, idx] in H_.get("boarded", [])
    open_frac = next(
        (d[2] for d in H_.get("door_open", []) if d[0] == fc.name and d[1] == idx), 0.0
    )
    if kind == "wall":
        siding(fc, u0, u1, v_f, v_f + WAIN)
        fc.box("frame", (u0 + u1) / 2, v_f + WAIN, 0.0, u1 - u0, 0.35, 0.5)  # nuki rail
        plaster(fc, u0, u1, v_f + WAIN + 0.17, TOP - 0.6)
    elif kind == "window":
        s0, s1 = v_f + H_["sill_height"], v_f + H_["sill_height"] + H_["window_height"]
        siding(fc, u0, u1, v_f, s0)
        fc.box("frame", (u0 + u1) / 2, s0, 0.0, u1 - u0, 0.3, 0.55)  # sill
        fc.box("frame", (u0 + u1) / 2, s1, 0.0, u1 - u0, 0.3, 0.55)  # head
        lattice(fc, u0, u1, s0 + 0.15, s1 - 0.15)
        plaster(fc, u0, u1, s1 + 0.15, TOP - 0.6)
        if boarded:
            for k in range(4):
                v = s0 + 0.5 + k * (H_["window_height"] - 1.0) / 3
                fc.box(
                    "boards",
                    (u0 + u1) / 2,
                    v,
                    0.42,
                    u1 - u0 + 0.6,
                    0.55,
                    0.1,
                    tilt=rng.uniform(-0.12, 0.12),
                )
    elif kind == "door":
        top = v_f + H_["door_height"]
        fc.box("frame", (u0 + u1) / 2, top, 0.0, u1 - u0, 0.35, 0.55)  # lintel
        fc.box(
            "frame", (u0 + u1) / 2, v_f + 0.1, 0.0, u1 - u0, 0.2, 0.6
        )  # threshold rail
        plaster(fc, u0, u1, top + 0.17, TOP - 0.6)
        half = (u1 - u0) / 2
        # left panel fixed; right panel slid left by open_frac (behind the left one)
        door_panel(fc, u0, u0 + half, v_f + 0.2, top - 0.17, 0.05)
        shift = half * open_frac
        door_panel(fc, u0 + half - shift, u1 - shift, v_f + 0.2, top - 0.17, -0.2)


def build_facade(fc, bays):
    n = len(bays)
    bw = fc.L / n
    for i in range(n):  # posts (corner post at i=0 belongs to this facade)
        u = -fc.L / 2 + i * bw
        fc.box("frame", u, F + WH / 2, 0.0, P, WH, P, bevel=0.03)
    fc.box("frame", 0, TOP - 0.3, 0.05, fc.L + P, 0.6, 0.7, bevel=0.03)  # top plate
    fc.box("frame", 0, F + 0.15, 0.05, fc.L + P, 0.3, 0.6)  # sill plate
    for i, kind in enumerate(bays):
        u0 = -fc.L / 2 + i * bw + P / 2
        u1 = -fc.L / 2 + (i + 1) * bw - P / 2
        bay(fc, kind, i, u0, u1)


facades = {
    "front": Facade("front", (0, -D / 2, 0), (1, 0, 0), (0, -1, 0), W),
    "back": Facade("back", (0, D / 2, 0), (-1, 0, 0), (0, 1, 0), W),
    "left": Facade("left", (-W / 2, 0, 0), (0, 1, 0), (-1, 0, 0), D),
    "right": Facade("right", (W / 2, 0, 0), (0, -1, 0), (1, 0, 0), D),
}
for name, fc in facades.items():
    build_facade(fc, H_["facades"][name])

# ------------------------------------------------------------------ base, floor, engawa
wbox("foundation", (0, 0, (F - 0.2) / 2), (W + 0.4, D + 0.4, F - 0.2))
wbox("engawa", (0, 0, F - 0.1), (W - 0.2, D - 0.2, 0.2))  # interior floor
ED = H_["engawa_depth"]
y_out = -D / 2 - ED
k = 0
y = -D / 2 - 0.3
while y > y_out + 0.25:
    if not chance("missing_engawa_planks"):
        wbox("engawa", (0, y, F - 0.12), (W + 0.6, 0.46, 0.18), bevel=0.02)
    y -= 0.5
    k += 1
wbox("engawa", (0, y_out + 0.15, F - 0.35), (W + 0.6, 0.3, 0.4))  # edge beam
x = -W / 2
while x <= W / 2 + 0.01:
    wbox("engawa", (x, y_out + 0.4, (F - 0.4) / 2 + 0.3), (0.45, 0.45, F - 0.7))
    wbox("foundation", (x, y_out + 0.4, 0.15), (0.9, 0.9, 0.3), bevel=0.05)
    x += W / 6
door_x = -W / 2 + (2.5) * (W / len(H_["facades"]["front"]))
wbox(
    "foundation", (door_x, y_out - 0.6, 0.25), (2.6, 1.2, 0.5), bevel=0.08
)  # step stone


# ------------------------------------------------------------------ gable ends (triangles)
def gable(x_sign):
    x = x_sign * W / 2
    t = 0.3
    verts, faces = [], []
    for dx in (-t / 2, t / 2):
        verts += [(x + dx, -D / 2, TOP), (x + dx, D / 2, TOP), (x + dx, 0, ZR - 0.2)]
    faces = [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
    me = bpy.data.meshes.new("gable")
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new("gable", me)
    scene.collection.objects.link(o)
    lp.activate(o)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    PARTS["gable"].append(o)
    fc = facades["left" if x_sign < 0 else "right"]
    fc.box("frame", 0, TOP + 0.3, 0.25, D, 0.5, 0.4)  # tie beam
    fc.box("frame", 0, TOP + R / 2, 0.25, 0.5, R, 0.4)  # king post
    for s in (-1, 1):  # struts
        fc.box("frame", s * D / 4, TOP + R / 4, 0.25, 0.35, R / 2, 0.35)


gable(-1)
gable(1)

# ------------------------------------------------------------------ roof
RUN = D / 2 + EAVE
SLAB_L = RUN / math.cos(PITCH)
LX = W + 2 * GOV
roof_objs = []


def slope_frame(side):
    """down-slope dir d, up normal n, ridge point."""
    d = Vector((0, side * math.cos(PITCH), -math.sin(PITCH)))
    n = Vector((1, 0, 0)).cross(d)
    if n.z < 0:
        n = -n
    return d, n, Vector((0, 0, ZR))


for side, tiles_tag in ((-1, "tiles_front"), (1, "tiles_back")):
    d, n, ridge = slope_frame(side)
    rot = (-side * PITCH, 0, 0)
    mid = ridge + d * (SLAB_L / 2)
    roof_objs.append(wbox("roof_base", mid, (LX, SLAB_L, 0.4), rot=rot))
    # tile rows: overlapping tapered segments, sunk half into the slab
    seg = 2.5
    nrows = int(LX / 0.6)
    for r in range(nrows):
        xr = -LX / 2 + 0.3 + r * 0.6
        s = 0.3
        while s < SLAB_L - 0.2:
            L_ = min(seg + 0.15, SLAB_L - s)
            last = s + seg >= SLAB_L - 0.2
            if chance("missing_tiles"):
                s += seg
                continue
            slip = rng.uniform(0.3, 1.2) if chance("slipped_tiles") else 0.0
            c = ridge + d * (s + L_ / 2 + slip) + n * 0.2 + Vector((xr, 0, 0))
            bpy.ops.mesh.primitive_cone_add(
                vertices=10 if last else 8,
                radius1=0.29,
                radius2=0.25,
                depth=L_,
                end_fill_type="NGON" if last else "NOTHING",
                location=c,
            )
            o = bpy.context.active_object
            o.rotation_euler = Vector((0, 0, 1)).rotation_difference(d).to_euler()
            PARTS[tiles_tag].append(o)
            roof_objs.append(o)
            s += seg
    # fascia along the eave + rafter ends under the eave
    eave_pt = ridge + d * SLAB_L
    roof_objs.append(wbox("eaves", eave_pt - n * 0.35, (LX, 0.15, 0.6), rot=rot))
    xr = -LX / 2 + 0.6
    while xr < LX / 2 - 0.3:
        c = ridge + d * (SLAB_L - 1.0) - n * 0.38 + Vector((xr, 0, 0))
        roof_objs.append(wbox("eaves", c, (0.28, 2.0, 0.32), rot=rot))
        xr += 1.2
    for gx in (-1, 1):  # barge boards at the gable overhang
        c = mid + Vector((gx * (LX / 2 - 0.1), 0, 0)) - n * 0.3
        roof_objs.append(wbox("eaves", c, (0.2, SLAB_L, 0.6), rot=rot))

roof_objs.append(wbox("ridge", (0, 0, ZR + 0.45), (LX + 0.2, 0.9, 0.7), bevel=0.05))
bpy.ops.mesh.primitive_cylinder_add(
    vertices=12,
    radius=0.38,
    depth=LX + 0.4,
    location=(0, 0, ZR + 0.85),
    rotation=(0, math.pi / 2, 0),
)
PARTS["ridge"].append(bpy.context.active_object)
roof_objs.append(bpy.context.active_object)
for gx in (-1, 1):  # onigawara end blocks
    roof_objs.append(
        wbox("ridge", (gx * (LX / 2 + 0.15), 0, ZR + 0.9), (0.45, 1.6, 1.7), bevel=0.08)
    )

# roof sag: apply transforms, then drop vertices toward the middle of the ridge
import bmesh  # noqa: E402

sag = DMG.get("roof_sag", 0.0)
if sag:
    for o in roof_objs:
        lp.activate(o)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        if o.dimensions.x > 3:  # long pieces need cuts along X or they can't bend
            bm = bmesh.new()
            bm.from_mesh(o.data)
            xs = [vv.co.x for vv in bm.verts]
            x = min(xs) + 1.5
            while x < max(xs) - 0.1:
                geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
                bmesh.ops.bisect_plane(
                    bm, geom=geom, plane_co=(x, 0, 0), plane_no=(1, 0, 0)
                )
                x += 1.5
            bm.to_mesh(o.data)
            bm.free()
        for vtx in o.data.vertices:
            t = max(0.0, 1 - (2 * vtx.co.x / LX) ** 2)
            height = max(0.0, min(1.0, (vtx.co.z - TOP + 1.5) / (ZR - TOP + 1.5)))
            vtx.co.z -= sag * t * (0.4 + 0.6 * height)

print(
    f"[house] built {sum(len(v) for v in PARTS.values())} pieces in {time.time() - T0:.0f}s"
)

# ------------------------------------------------------------------ join, bake, export
meshes = lp.join_parts(PARTS, spec, {"W": W, "H": ZR}, "House")
BIG = {
    "siding",
    "plaster",
    "tiles_front",
    "tiles_back",
    "roof_base",
    "foundation",
    "frame",
    "engawa",
}
bake_s = lp.bake(
    meshes, os.path.join(OUT, "textures"), lambda tag: 1024 if tag in BIG else 512
)
print(f"[house] bake took {bake_s:.0f}s")
lp.swap_to_baked(meshes)
lp.export_fbx(meshes, os.path.join(OUT, "house.fbx"))
total_tris = sum(me["tris"] for me in meshes)
print(f"[house] exported {len(meshes)} meshes, {total_tris} tris total")


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
# a dark interior so the openings read as depth
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, F + WH / 2))
inner = bpy.context.active_object
inner.scale = (W - 1.4, D - 1.4, WH - 0.2)
bpy.ops.object.transform_apply(scale=True)
inner.data.materials.append(plain("Interior", "#0C0A09"))

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
scene.cycles.samples = 64
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = 1400, 900

shots = (
    ("preview_wide", (-30, -42, 14), (0, 0, 7), 35),
    ("preview_front", (2, -30, 5.5), (2, 0, 7), 40),
    ("preview_close", (door_x - 6, -D / 2 - 11, 4.5), (door_x - 3.5, -D / 2, 5), 45),
    ("preview_roof", (24, -22, 26), (2, 0, 13), 40),
)
for name, loc, tgt, lens in shots:
    lp.look(cam, target, loc, tgt, lens)
    scene.render.filepath = os.path.join(OUT, f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print(f"[house] rendered {name}")
print(f"[house] done in {time.time() - T0:.0f}s -> {OUT}")
