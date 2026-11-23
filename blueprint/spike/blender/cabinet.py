"""
THROWAWAY SPIKE: Blender -> Studio. Builds a modern cabinet procedurally.

Run headless:
  blender -b -P cabinet.py -- <out_dir>

Outputs:
  <out_dir>/cabinet.fbx   import into Studio (3D Importer)
  <out_dir>/cabinet.png   preview render

Units: 1 Blender unit = 1 Roblox stud.
"""

import math
import os
import sys

import bpy

OUT = (
    sys.argv[sys.argv.index("--") + 1]
    if "--" in sys.argv
    else os.path.dirname(__file__)
)
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- dimensions (studs)
W, D = 4.2, 1.6  # carcass width, depth
LEG_H = 0.55  # leg height
BODY_H = 2.45  # carcass height (total ~3.0)
PANEL_T = 0.06  # thickness of door/drawer fronts
GAP = 0.025  # seam between fronts
FRAME = 0.06  # visible carcass edge around the fronts
DRAWER_COL_W = 1.4  # left column: 3 drawers; right: 2 doors
BEVEL = 0.012

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def material(name, color, metallic=0.0, rough=0.5):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.metallic = metallic
    m.roughness = rough
    return m


WOOD = material("Wood", (0.42, 0.27, 0.15), rough=0.6)
METAL = material("Metal", (0.08, 0.08, 0.08), metallic=1.0, rough=0.35)

wood_parts, metal_parts = [], []


def box(name, size, loc, mat, bevel=BEVEL):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        mod = o.modifiers.new("Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        mod.limit_method = "ANGLE"
    o.data.materials.append(mat)
    (wood_parts if mat is WOOD else metal_parts).append(o)
    return o


def handle(name, length, center, vertical):
    """Slim bar handle with two standoffs, sticking out of the front (-Y)."""
    x, y, z = center
    r = 0.022
    bar_y = y - 0.09
    rot = (0, 0, 0) if vertical else (0, math.pi / 2, 0)
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=16, radius=r, depth=length, location=(x, bar_y, z), rotation=rot
    )
    bar = bpy.context.active_object
    bar.name = name
    bar.data.materials.append(METAL)
    metal_parts.append(bar)
    for s in (-1, 1):
        off = s * (length / 2 - 0.05)
        loc = (x, y - 0.045, z + off) if vertical else (x + off, y - 0.045, z)
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=12,
            radius=0.016,
            depth=0.09,
            location=loc,
            rotation=(math.pi / 2, 0, 0),
        )
        st = bpy.context.active_object
        st.data.materials.append(METAL)
        metal_parts.append(st)


# ---------------------------------------------------------------- carcass
z0 = LEG_H
front_y = -D / 2
box("Top", (W + 0.08, D + 0.06, 0.08), (0, 0, z0 + BODY_H - 0.04), WOOD)
box("Bottom", (W, D, 0.08), (0, 0, z0 + 0.04), WOOD)
box("SideL", (0.06, D, BODY_H - 0.16), (-W / 2 + 0.03, 0, z0 + BODY_H / 2), WOOD)
box("SideR", (0.06, D, BODY_H - 0.16), (W / 2 - 0.03, 0, z0 + BODY_H / 2), WOOD)
box("Back", (W - 0.12, 0.04, BODY_H - 0.16), (0, D / 2 - 0.02, z0 + BODY_H / 2), WOOD)
divider_x = -W / 2 + FRAME + DRAWER_COL_W
box(
    "Divider",
    (0.05, D - 0.06, BODY_H - 0.16),
    (divider_x, -0.02, z0 + BODY_H / 2),
    WOOD,
)
# recessed plinth line under the fronts
box("Rail", (W - 0.12, 0.05, 0.06), (0, front_y + 0.06, z0 + 0.11), WOOD)

# ---------------------------------------------------------------- fronts
inner_bottom = z0 + 0.14
inner_top = z0 + BODY_H - 0.1
inner_h = inner_top - inner_bottom
fy = front_y - PANEL_T / 2 + 0.01

# 3 drawers (left column), slightly graduated: small, medium, large from top
x0 = -W / 2 + FRAME
x1 = divider_x - 0.025
ratios = [0.28, 0.33, 0.39]
z = inner_top
for i, r in enumerate(ratios):
    h = inner_h * r
    cz = z - h / 2
    box(
        f"Drawer{i + 1}",
        (x1 - x0 - GAP, PANEL_T, h - GAP),
        ((x0 + x1) / 2, fy, cz),
        WOOD,
    )
    handle(
        f"DrawerHandle{i + 1}",
        0.55,
        ((x0 + x1) / 2, fy - PANEL_T / 2, cz + h * 0.22),
        vertical=False,
    )
    z -= h

# 2 doors (right column)
dx0 = divider_x + 0.025
dx1 = W / 2 - FRAME
door_w = (dx1 - dx0) / 2
for i in range(2):
    cx = dx0 + door_w * (i + 0.5)
    box(
        f"Door{i + 1}",
        (door_w - GAP, PANEL_T, inner_h - GAP),
        (cx, fy, inner_bottom + inner_h / 2),
        WOOD,
    )
    # shallow routed groove frame on each door (inset panel look)
    box(
        f"DoorInset{i + 1}",
        (door_w - 0.3, 0.012, inner_h - 0.3),
        (cx, fy - PANEL_T / 2 - 0.004, inner_bottom + inner_h / 2),
        WOOD,
        bevel=0.004,
    )
    hx = cx + (door_w / 2 - 0.14) * (1 if i == 0 else -1)
    handle(
        f"DoorHandle{i + 1}",
        0.7,
        (hx, fy - PANEL_T / 2, inner_bottom + inner_h * 0.62),
        vertical=True,
    )

# ---------------------------------------------------------------- tapered, splayed legs
for sx in (-1, 1):
    for sy in (-1, 1):
        bpy.ops.mesh.primitive_cone_add(
            vertices=16,
            radius1=0.035,
            radius2=0.075,
            depth=LEG_H + 0.02,
            location=(sx * (W / 2 - 0.22), sy * (D / 2 - 0.2), LEG_H / 2),
        )
        leg = bpy.context.active_object
        leg.name = "Leg"
        leg.rotation_euler = (-sy * math.radians(6), sx * math.radians(6), 0)
        leg.data.materials.append(WOOD)
        wood_parts.append(leg)
        # metal foot cap
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=16,
            radius=0.038,
            depth=0.04,
            location=(
                sx * (W / 2 - 0.22) - sx * 0.03,
                sy * (D / 2 - 0.2) - sy * 0.03,
                0.02,
            ),
        )
        cap = bpy.context.active_object
        cap.data.materials.append(METAL)
        metal_parts.append(cap)


# ---------------------------------------------------------------- join by material
def join(parts, name):
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
        bpy.context.view_layer.objects.active = p
        for m in list(p.modifiers):
            bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    o.name = name
    o.data.name = name
    return o


wood = join(wood_parts, "Cabinet_Wood")
metal = join(metal_parts, "Cabinet_Metal")

# origin at the floor, center of the footprint
for o in (wood, metal):
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


print(f"[cabinet] Cabinet_Wood tris={tris(wood)}  Cabinet_Metal tris={tris(metal)}")

# ---------------------------------------------------------------- export FBX
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.fbx(
    filepath=os.path.join(OUT, "cabinet.fbx"),
    use_selection=True,
    apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_UNITS",
    axis_forward="-Z",
    axis_up="Y",
    mesh_smooth_type="FACE",
)

# ---------------------------------------------------------------- preview render
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
cam.location = (-4.2, -6.0, 3.4)
target = bpy.data.objects.new("Target", None)
target.location = (0, 0, 1.4)
scene.collection.objects.link(target)
c = cam.constraints.new("TRACK_TO")
c.target = target
c.track_axis = "TRACK_NEGATIVE_Z"
c.up_axis = "UP_Y"
cam_data.lens = 50
scene.camera = cam

scene.render.engine = "BLENDER_WORKBENCH"
shading = scene.display.shading
shading.light = "STUDIO"
shading.color_type = "MATERIAL"
shading.show_cavity = True
shading.cavity_type = "BOTH"
shading.show_shadows = True
scene.display.render_aa = "8"
scene.render.resolution_x = 1200
scene.render.resolution_y = 900
scene.render.filepath = os.path.join(OUT, "cabinet.png")
bpy.ops.render.render(write_still=True)
print("[cabinet] done ->", OUT)
