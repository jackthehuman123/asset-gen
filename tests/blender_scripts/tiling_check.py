"""Runs inside Blender: seamless tile, UV scale, grain UVs, cache reuse."""

import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import bpy  # noqa: E402
import numpy as np  # noqa: E402

from rbxasset.blender import tiling  # noqa: E402

WOOD = {"type": "wood", "base": "#8a5a2b", "grain": "#4a2c10"}
STONE = {
    "type": "stone",
    "color_a": "#808080",
    "color_b": "#909090",
    "mortar": "#202020",
    "cell_scale": 4.0,
}


def check(cond, msg):
    if not cond:
        print("FAIL:", msg)
        sys.exit(1)


def load(path):
    img = bpy.data.images.load(path)
    n = img.size[0]
    return np.array(img.pixels[:]).reshape(n, n, 4)[:, :, :3]


tmp = tempfile.mkdtemp()
for name, fin in (("wood", WOOD), ("stone", STONE)):
    paths = tiling.bake_tile(name, fin, {}, 4.0, 256, tmp)
    check({"color", "roughness", "normal"} <= set(paths), f"{name} kinds {set(paths)}")
    px = load(paths["color"])
    check(px.std() > 0.01, f"{name} constant")
    col = np.abs(px[:, 0] - px[:, -1]).mean()
    row = np.abs(px[0] - px[-1]).mean()
    inner_c = np.abs(np.diff(px[:, 1:-1], axis=1)).mean()
    inner_r = np.abs(np.diff(px[1:-1], axis=0)).mean()
    print(name, "seam", col, row, "interior", inner_c, inner_r)
    # brief: seam < 0.02, or within 3x the adjacent-interior difference for
    # finishes whose own pixel-to-pixel variation already exceeds 0.02/3
    check(
        col < max(0.02, inner_c * 3) and row < max(0.02, inner_r * 3),
        f"{name} seam col={col:.4f} row={row:.4f}",
    )
    check(
        col < inner_c * 3 + 0.02 and row < inner_r * 3 + 0.02,
        f"{name} seam vs interior",
    )


metal = tiling.bake_tile("m", {"type": "metal", "color": "#9a9a9a"}, {}, 4.0, 64, tmp)
check("metalness" in metal and Path(metal["metalness"]).exists(), "metalness png")

# cache
m0 = {k: Path(p).stat().st_mtime_ns for k, p in paths.items()}
t = time.time()
again = tiling.bake_tile("stone", STONE, {}, 4.0, 256, tmp)
check(time.time() - t < 1.0, "cache slow")
check(
    again == paths and {k: Path(p).stat().st_mtime_ns for k, p in again.items()} == m0,
    "cache rewrote",
)


def box(dims, grain=None):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object
    o.scale = dims
    bpy.ops.object.transform_apply(scale=True)
    if grain is not None:
        a = o.data.attributes.new("grain", "INT", "POINT")
        for d in a.data:
            d.value = grain
    return o


def extent(o, poly_dir):
    uv = o.data.uv_layers["UVMap"].data
    for p in o.data.polygons:
        if abs(p.normal[1] - poly_dir) < 1e-3:
            us = [uv[i].uv for i in p.loop_indices]
            return (
                max(u[0] for u in us) - min(u[0] for u in us),
                max(u[1] for u in us) - min(u[1] for u in us),
            )


o = box((12, 1, 8))
tiling.tile_uvs(o, 4)
eu, ev = extent(o, -1)
check(abs(eu - 3.0) < 0.01 and abs(ev - 2.0) < 0.01, f"scale {eu} {ev}")

o = box((0.45, 0.12, 4), grain=2)
tiling.tile_uvs(o, 4)
eu, ev = extent(o, -1)
check(abs(eu - 1.0) < 0.01 and abs(ev - 0.1125) < 0.001, f"grain {eu} {ev}")
print("tiling_check OK")
