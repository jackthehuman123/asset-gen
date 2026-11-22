"""Telephone box geometry (a K6-style kiosk: corner posts, glazing bars, domed roof).
Runs inside Blender. Units: studs. Front (the door) faces -Y, ground at z=0."""
import random
from typing import Dict

import bmesh
import bpy

from rbxasset.builders.result import BuildResult

TAGS = ("base", "frame", "door", "roof", "sign", "glazing", "handle")
BAR, RAIL_LOW, RAIL_TOP, ROOF_T, BEVEL = 0.06, 0.55, 0.15, 0.12, 0.01
GRID = 12  # roof grid cells per side


def build(params: Dict, rng: random.Random) -> BuildResult:
    W, D, H = params["width"], params["depth"], params["height"]
    PL, P = params["plinth_height"], params["post_size"]
    COLS, ROWS = params["pane_cols"], params["pane_rows"]
    RISE, SIGN = params["roof_rise"], params["sign_height"]
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

    z_lo, z_hi = PL + RAIL_LOW, H - SIGN - RAIL_TOP
    row_h = (z_hi - z_lo) / ROWS
    for side in ("front", "back", "left", "right"):
        tag = "door" if side == "front" else "frame"
        L = W if side in ("front", "back") else D
        inner = L - 2 * P
        col_w = inner / COLS
        wall_box(tag, side, 0, PL + RAIL_LOW / 2, inner, RAIL_LOW, 0.1)  # bottom rail
        wall_box(tag, side, 0, z_hi + RAIL_TOP / 2, inner, RAIL_TOP, 0.1)  # top rail
        for i in range(1, COLS):  # mullions
            wall_box(tag, side, -inner / 2 + i * col_w, (z_lo + z_hi) / 2, BAR, z_hi - z_lo, 0.08)
        for j in range(1, ROWS):  # glazing bars
            wall_box(tag, side, 0, z_lo + j * row_h, inner, BAR * 0.8, 0.08)
        if params["glazing"]:
            for i in range(COLS):
                for j in range(ROWS):
                    wall_box("glazing", side, -inner / 2 + (i + 0.5) * col_w, z_lo + (j + 0.5) * row_h,
                             col_w - BAR, row_h - BAR * 0.8, 0.02, bevel=0.0)
        wall_box("sign", side, 0, H - SIGN / 2, inner, SIGN, 0.08, off=0.02)
    # door handle: a vertical bar on the front, right side
    box("handle", (0.04, 0.05, 1.1), (W / 2 - P - 0.15, -(D / 2 + 0.06), PL + RAIL_LOW + 1.6), bevel=0.0)

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
    roof = bpy.data.objects.new("roof", mesh)
    bpy.context.scene.collection.objects.link(roof)
    parts["roof"].append(roof)

    total_h = H + ROOF_T + RISE
    shots = [
        ("wide", (-W * 2.9, -D * 4.8, total_h * 0.6), (0.0, 0.0, total_h * 0.48), 40.0),
        ("close", (-W * 0.9, -D * 2.2, total_h * 0.62), (0.0, -D / 2, total_h * 0.6), 50.0),
    ]
    return BuildResult(parts, shots, {"W": W, "H": total_h})
