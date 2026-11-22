"""Telephone box geometry (a K6-style kiosk: corner posts, glazing bars, domed roof).
Runs inside Blender. Units: studs. Front (the door) faces -Y, ground at z=0."""
import random
from typing import Dict

import bmesh
import bpy

from rbxasset.builders.result import BuildResult

TAGS = ("base", "frame", "door", "roof", "sign", "glazing", "handle")
BAR, RAIL_TOP, ROOF_T, BEVEL = 0.06, 0.15, 0.12, 0.01
GRID = 12  # roof grid cells per side


def build(params: Dict, rng: random.Random) -> BuildResult:
    W, D, H = params["width"], params["depth"], params["height"]
    PL, P = params["plinth_height"], params["post_size"]
    COLS, ROWS = params["pane_cols"], params["pane_rows"]
    RISE, SIGN, LOW = params["roof_rise"], params["sign_height"], params["lower_panel_height"]
    parts = {k: [] for k in TAGS}

    def box(tag, size, loc, bevel=BEVEL):
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
        o = bpy.context.active_object
        o.scale = size
        bpy.ops.object.transform_apply(scale=True)
        if bevel:
            m = o.modifiers.new("Bevel", "BEVEL")
            m.width, m.segments, m.limit_method = bevel, 1, "ANGLE"
        parts[tag].append(o)

    def wall_box(tag, side, u, z, su, sz, sw, off=0.0, bevel=BEVEL):
        """Box on a wall: u along the wall, z up, sw thickness; off moves it outward."""
        if side in ("front", "back"):
            n = -1 if side == "front" else 1
            loc, size = (u, n * (D / 2 - P / 2 + off), z), (su, sw, sz)
        else:
            n = -1 if side == "left" else 1
            loc, size = (n * (W / 2 - P / 2 + off), u, z), (sw, su, sz)
        box(tag, size, loc, bevel)

    # stepped base and corner posts
    box("base", (W + 0.12, D + 0.12, PL), (0, 0, PL / 2))
    for sx in (-1, 1):
        for sy in (-1, 1):
            box("frame", (P, P, H - PL), (sx * (W / 2 - P / 2), sy * (D / 2 - P / 2), PL + (H - PL) / 2))

    z_lo, z_hi = PL + LOW, H - SIGN - RAIL_TOP
    row_h = (z_hi - z_lo) / ROWS
    for side in ("front", "back", "left", "right"):
        tag = "door" if side == "front" else "frame"
        L = W if side in ("front", "back") else D
        inner = L - 2 * P
        col_w = inner / COLS
        wall_box(tag, side, 0, PL + LOW / 2, inner, LOW, 0.1)  # bottom rail
        for i in range(COLS):  # raised lower panels
            wall_box(tag, side, -inner / 2 + (i + 0.5) * col_w, PL + LOW / 2,
                     col_w - 0.16, LOW - 0.2, 0.05, off=0.06)
        wall_box(tag, side, 0, z_hi + RAIL_TOP / 2, inner, RAIL_TOP, 0.1)  # top rail
        for i in range(1, COLS):  # mullions
            wall_box(tag, side, -inner / 2 + i * col_w, (z_lo + z_hi) / 2, BAR, z_hi - z_lo, 0.08)
        for j in range(1, ROWS):  # glazing bars
            wall_box(tag, side, 0, z_lo + j * row_h, inner, BAR * 0.8, 0.08)
        if side == "front":  # heavier door stiles
            for sgn in (-1, 1):
                wall_box("door", side, sgn * (inner / 2 - 0.07), (z_lo + z_hi) / 2, 0.14, z_hi - z_lo, 0.1, off=0.02)
        if params["glazing"]:
            for i in range(COLS):
                for j in range(ROWS):
                    wall_box("glazing", side, -inner / 2 + (i + 0.5) * col_w, z_lo + (j + 0.5) * row_h,
                             col_w - BAR, row_h - BAR * 0.8, 0.02, bevel=0.0)
        # sign: panel, border, crown, and block letters either side of it
        wall_box("sign", side, 0, H - SIGN / 2, inner, SIGN, 0.08, off=0.02)
        for dz in (0.03, SIGN - 0.03):
            wall_box("sign", side, 0, H - dz, inner, 0.05, 0.03, off=0.07, bevel=0.0)
        for sgn in (-1, 1):
            wall_box("sign", side, sgn * (inner / 2 - 0.025), H - SIGN / 2, 0.05, SIGN, 0.03, off=0.07, bevel=0.0)
        cz = H - SIGN * 0.58
        wall_box("sign", side, 0, cz - 0.1, 0.56, 0.07, 0.03, off=0.08, bevel=0.0)  # crown band
        for k in range(-2, 3):  # crown points, tallest in the middle
            wall_box("sign", side, k * 0.12, cz - 0.02, 0.06, 0.2 if k == 0 else 0.15 if abs(k) == 1 else 0.11,
                     0.03, off=0.08, bevel=0.0)
        wall_box("sign", side, 0, cz + 0.1, 0.26, 0.04, 0.03, off=0.08, bevel=0.0)  # arch bar
        wall_box("sign", side, 0, cz + 0.17, 0.08, 0.08, 0.03, off=0.08, bevel=0.0)  # orb
        for k in range(4):  # block letters
            for sgn in (-1, 1):
                wall_box("sign", side, sgn * (0.55 + k * 0.12), H - SIGN * 0.5, 0.05, SIGN * 0.32, 0.02,
                         off=0.08, bevel=0.0)
    # cornice: two stepped mouldings under the roof edge
    box("roof", (W + 0.22, D + 0.22, 0.07), (0, 0, H - 0.035), bevel=0.0)
    box("roof", (W + 0.14, D + 0.14, 0.07), (0, 0, H - 0.105), bevel=0.0)
    # door: handle bar, handle plate, three hinges on the left edge
    hx = W / 2 - P - 0.15
    box("handle", (0.04, 0.05, 1.1), (hx, -(D / 2 + 0.06), z_lo + 1.0), bevel=0.0)
    box("handle", (0.14, 0.02, 1.3), (hx, -(D / 2 + 0.045), z_lo + 1.0), bevel=0.0)
    for f in (0.15, 0.5, 0.85):
        bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.035, depth=0.2,
                                            location=(-(W / 2 - P - 0.02), -(D / 2 + 0.04), z_lo + f * (z_hi - z_lo)))
        parts["handle"].append(bpy.context.active_object)

    # domed roof: closed slab whose top is a pillow z = rise*(1-x^2)(1-y^2)
    rx, ry, z0 = W / 2 + 0.12, D / 2 + 0.12, H
    pts = [-1 + 2 * i / GRID for i in range(GRID + 1)]
    top = [[(rx * x, ry * y, z0 + ROOF_T + RISE * (1 - x * x) * (1 - y * y)) for y in pts] for x in pts]
    bot = [[(rx * x, ry * y, z0) for y in pts] for x in pts]
    verts, idx = [], {}
    for layer, grid in (("t", top), ("b", bot)):
        for i in range(GRID + 1):
            for j in range(GRID + 1):
                idx[(layer, i, j)] = len(verts)
                verts.append(grid[i][j])
    faces = []
    for i in range(GRID):
        for j in range(GRID):
            for layer in ("t", "b"):
                faces.append([idx[(layer, i, j)], idx[(layer, i + 1, j)],
                              idx[(layer, i + 1, j + 1)], idx[(layer, i, j + 1)]])
    for k in range(GRID):  # side walls between the top and bottom edge rings
        for a, b in (((k, 0), (k + 1, 0)), ((k, GRID), (k + 1, GRID)),
                     ((0, k), (0, k + 1)), ((GRID, k), (GRID, k + 1))):
            faces.append([idx[("t",) + a], idx[("t",) + b], idx[("b",) + b], idx[("b",) + a]])
    mesh = bpy.data.meshes.new("roof")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = True
    roof = bpy.data.objects.new("roof", mesh)
    bpy.context.scene.collection.objects.link(roof)
    parts["roof"].append(roof)

    total_h = H + ROOF_T + RISE
    shots = [
        ("wide", (-W * 2.9, -D * 4.8, total_h * 0.6), (0.0, 0.0, total_h * 0.48), 40.0),
        ("close", (-W * 0.9, -D * 2.2, total_h * 0.62), (0.0, -D / 2, total_h * 0.6), 50.0),
        ("sign", (-W * 0.6, -D * 2.0, H - 0.1), (0.0, -D / 2, H - SIGN / 2), 55.0),
    ]
    return BuildResult(parts, shots, {"W": W, "H": total_h})
