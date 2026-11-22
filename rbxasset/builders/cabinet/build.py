"""Cabinet geometry (ported from blueprint/spike/blender/cabinet_styled.py).
Runs inside Blender. Units: studs. Front faces -Y, ground at z=0."""
import math
import random
from typing import Dict

import bpy

from rbxasset.builders.result import BuildResult

PANEL_T, GAP, FRAME, BEVEL = 0.06, 0.025, 0.06, 0.012
TAGS = ("top", "carcass", "fronts", "handles", "legs", "foot_caps")


def build(params: Dict, rng: random.Random) -> BuildResult:
    W, D = params["width"], params["depth"]
    LEG_H, BODY_H = params["leg_height"], params["body_height"]
    DRAWER_COL_W = params["drawer_column_width"]
    parts = {k: [] for k in TAGS}

    def box(tag, size, loc, bevel=BEVEL):
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
        o = bpy.context.active_object
        o.scale = size
        bpy.ops.object.transform_apply(scale=True)
        if bevel:
            m = o.modifiers.new("Bevel", "BEVEL")
            m.width, m.segments, m.limit_method = bevel, 2, "ANGLE"
        parts[tag].append(o)
        return o

    def cyl(tag, r, depth, loc, rot, verts=16):
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
        parts[tag].append(bpy.context.active_object)

    def handle(length, center, vertical):
        x, y, z = center
        rot = (0, 0, 0) if vertical else (0, math.pi / 2, 0)
        cyl("handles", 0.022, length, (x, y - 0.09, z), rot)
        for s in (-1, 1):
            off = s * (length / 2 - 0.05)
            loc = (x, y - 0.045, z + off) if vertical else (x + off, y - 0.045, z)
            cyl("handles", 0.016, 0.09, loc, (math.pi / 2, 0, 0), verts=12)

    z0, front_y = LEG_H, -D / 2
    box("top", (W + 0.08, D + 0.06, 0.08), (0, 0, z0 + BODY_H - 0.04))
    box("carcass", (W, D, 0.08), (0, 0, z0 + 0.04))
    box("carcass", (0.06, D, BODY_H - 0.16), (-W / 2 + 0.03, 0, z0 + BODY_H / 2))
    box("carcass", (0.06, D, BODY_H - 0.16), (W / 2 - 0.03, 0, z0 + BODY_H / 2))
    box("carcass", (W - 0.12, 0.04, BODY_H - 0.16), (0, D / 2 - 0.02, z0 + BODY_H / 2))
    divider_x = -W / 2 + FRAME + DRAWER_COL_W
    box("carcass", (0.05, D - 0.06, BODY_H - 0.16), (divider_x, -0.02, z0 + BODY_H / 2))
    box("carcass", (W - 0.12, 0.05, 0.06), (0, front_y + 0.06, z0 + 0.11))

    inner_bottom, inner_top = z0 + 0.14, z0 + BODY_H - 0.1
    inner_h = inner_top - inner_bottom
    fy = front_y - PANEL_T / 2 + 0.01

    # drawer column (left)
    x0, x1 = -W / 2 + FRAME, divider_x - 0.025
    z = inner_top
    for r in (0.28, 0.33, 0.39):
        h = inner_h * r
        cz = z - h / 2
        box("fronts", (x1 - x0 - GAP, PANEL_T, h - GAP), ((x0 + x1) / 2, fy, cz))
        handle(min(0.6, (x1 - x0) * 0.4), ((x0 + x1) / 2, fy - PANEL_T / 2, cz + h * 0.18), vertical=False)
        z -= h

    # two doors (right)
    dx0, dx1 = divider_x + 0.025, W / 2 - FRAME
    door_w = (dx1 - dx0) / 2
    for i in range(2):
        cx = dx0 + door_w * (i + 0.5)
        box("fronts", (door_w - GAP, PANEL_T, inner_h - GAP), (cx, fy, inner_bottom + inner_h / 2))
        box("fronts", (door_w - 0.3, 0.012, inner_h - 0.3),
            (cx, fy - PANEL_T / 2 - 0.004, inner_bottom + inner_h / 2), bevel=0.004)
        hx = cx + (door_w / 2 - 0.14) * (1 if i == 0 else -1)
        handle(inner_h * 0.42, (hx, fy - PANEL_T / 2, inner_bottom + inner_h * 0.55), vertical=True)

    # splayed legs; base sits on z=0, top tucks 0.02 into the carcass bottom
    for sx in (-1, 1):
        for sy in (-1, 1):
            lx, ly = sx * (W / 2 - 0.22), sy * (D / 2 - 0.2)
            bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.035, radius2=0.075, depth=LEG_H + 0.02,
                                            location=(lx, ly, (LEG_H + 0.02) / 2))
            leg = bpy.context.active_object
            leg.rotation_euler = (-sy * math.radians(6), sx * math.radians(6), 0)
            parts["legs"].append(leg)
            tilt = math.tan(math.radians(6)) * LEG_H / 2
            cyl("foot_caps", 0.038, 0.04, (lx - sx * tilt, ly - sy * tilt, 0.02), (0, 0, 0))

    H = LEG_H + BODY_H
    shots = [
        ("wide", (-W * 1.05, -W * 1.6, 3.4), (0.0, 0.0, H * 0.6 + 0.5), 40.0),
        ("close", (-W / 2 + DRAWER_COL_W * 0.5 - 0.9, -D / 2 - 2.3, LEG_H + BODY_H * 0.65 + 0.7),
         (-W / 2 + DRAWER_COL_W * 0.5, -D / 2, LEG_H + BODY_H * 0.6), 50.0),
    ]
    return BuildResult(parts, shots, {"W": W, "H": H})
