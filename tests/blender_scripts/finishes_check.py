"""Runs inside Blender: builds each finish, bakes 64x64 maps via EMIT, asserts."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import bpy  # noqa: E402
import numpy as np  # noqa: E402

from rbxasset.blender import finishes  # noqa: E402

RES = 64
ALL_WEAR = {
    "water_stains": 0.8, "streaks": {"amount": 0.8, "color": "#2a2a2a"},
    "grime": 0.8, "edge": 0.8, "moss": {"amount": 0.8, "color": "#3a5a20"}, "dust": 0.8,
}
WOOD = {"type": "wood", "base": "#8a5a2b", "grain": "#4a2c10"}
PAINT = {"type": "paint", "color": "#d8cfc0"}
PLASTER = {"type": "paint", "color": "#d8cfc0", "mottle": 0.8, "cracks": 0.8}
METAL = {"type": "metal", "color": "#9a9a9a"}
STONE = {"type": "stone", "color_a": "#808080", "color_b": "#909090",
         "mortar": "#ff0000", "cell_scale": 4.0}


def make_cube():
    bpy.ops.mesh.primitive_cube_add(size=2)
    o = bpy.context.active_object
    attr = o.data.color_attributes.new(name="grain", type="FLOAT_COLOR", domain="POINT")
    for item in attr.data:
        item.color = (1.0, 0.0, 0.0, 1.0)
    return o


def bake(fn, socket_key, wear):
    o = make_cube()
    fn_nodes = finishes.make_finish("t", fn, wear, {"W": 2.0, "H": 2.0})
    o.data.materials.append(fn_nodes.mat)
    tree = fn_nodes.mat.node_tree
    img = bpy.data.images.new("bk", RES, RES, float_buffer=True)
    tex = tree.nodes.new("ShaderNodeTexImage")
    tex.image = img
    emit = tree.nodes.new("ShaderNodeEmission")
    tree.links.new(fn_nodes.sockets[socket_key], emit.inputs["Color"])
    tree.links.new(emit.outputs["Emission"], fn_nodes.out.inputs["Surface"])
    tree.nodes.active = tex
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 4
    sc.cycles.use_denoising = False
    bpy.ops.object.bake(type="EMIT")
    px = np.array(img.pixels[:]).reshape(-1, 4)[:, :3]
    bpy.data.objects.remove(o)
    return px


def check(cond, msg):
    if not cond:
        print("FAIL:", msg)
        sys.exit(1)


for label, fin, wear in [
    ("wood", WOOD, {}), ("paint", PAINT, {}), ("plaster", PLASTER, {}),
    ("metal", METAL, {}), ("stone", STONE, {}), ("wood+all_wear", WOOD, ALL_WEAR),
]:
    px = bake(fin, "color", wear)
    check(px.std() > 0.01, f"{label} color constant (std={px.std():.4f})")

px = bake(METAL, "metalness", {})
check(px.mean() > 0.5, f"metal metalness mean {px.mean():.3f}")

px = bake(STONE, "color", {})
mortar = ((px[:, 0] - px[:, 1]) > 0.3).sum()
cell = (np.abs(px[:, 0] - px[:, 1]) < 0.05).sum()
check(mortar > 0 and cell > 0, f"stone mortar={mortar} cell={cell}")

# rusted metal must still build and bake (rust fraction is not asserted: the AO
# crevice term saturates on a lone cube)
px = bake(dict(METAL, rust=0.4), "color", {})
check(px.std() > 0.01, "rusted metal color constant")

check(finishes.lin("#ffffff")[0] > 0.99, "lin white")
print("finishes_check OK")
