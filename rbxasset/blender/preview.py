"""Preview renders (not exported). Runs inside Blender."""
import math
import os
from typing import List, Tuple

import bpy
from mathutils import Vector

from . import executor
from .finishes import lin

PRESETS = ("bright_interior", "abandoned_interior", "overcast_exterior")


def _plain(name, hexstr, rough=0.85):
    mt = bpy.data.materials.new(name)
    mt.use_nodes = True
    b = mt.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = lin(hexstr)
    b.inputs["Roughness"].default_value = rough
    return mt


def _box(size, loc, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat)
    return o


def _world(color, strength):
    w = bpy.data.worlds.new("PreviewWorld")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = color
    bg.inputs["Strength"].default_value = strength
    bpy.context.scene.world = w


def _room(wall_hex, floor_hex, minz, back_y, rough_floor):
    _box((30, 30, 0.1), (0, 0, minz - 0.05), _plain("Floor", floor_hex, rough_floor))
    _box((30, 0.1, 12), (0, back_y + 0.6, minz + 6), _plain("Wall", wall_hex, 0.95))


def _setup_lighting(preset, bounds):
    lo, hi = bounds["min"], bounds["max"]
    cx = (lo[0] + hi[0]) / 2
    if preset == "overcast_exterior":
        bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, lo[2]))
        bpy.context.active_object.data.materials.append(_plain("Ground", "#4A4636", 0.9))
        _world((0.62, 0.66, 0.72, 1), 0.9)
        bpy.ops.object.light_add(type="SUN", location=(0, 0, 50))
        sun = bpy.context.active_object
        sun.data.energy = 1.6
        sun.data.angle = math.radians(8)
        sun.rotation_euler = (math.radians(55), 0, math.radians(-35))
        return
    key_loc = (cx - 5, lo[1] - 6, lo[2] + 6)
    if preset == "abandoned_interior":
        _room("#857D6E", "#77704F", lo[2], hi[1], 0.9)
        _world((0.55, 0.6, 0.7, 1), 0.08)
    else:
        _room("#F4F2EE", "#D9CBB6", lo[2], hi[1], 0.6)
        _world((0.9, 0.9, 0.92, 1), 0.6)
    bpy.ops.object.light_add(type="AREA", location=key_loc)
    key = bpy.context.active_object
    key.data.size = 5
    key.rotation_euler = (math.radians(50), 0, math.radians(-40))
    if preset == "abandoned_interior":
        key.data.energy = 500
        key.data.color = (0.75, 0.82, 1.0)
        bpy.ops.object.light_add(type="POINT", location=(cx + 3, lo[1] + 2.5, lo[2] + 2.5))
        fill = bpy.context.active_object
        fill.data.energy = 25
        fill.data.color = (1.0, 0.75, 0.5)
    else:
        key.data.energy = 900


def render_shots(shots, preset: str, out_dir: str, samples: int,
                 res: Tuple[int, int], bounds) -> List[str]:
    if preset not in PRESETS:
        raise ValueError("unknown preview preset %r; available: %s" % (preset, ", ".join(PRESETS)))
    os.makedirs(out_dir, exist_ok=True)
    lo, hi = bounds["min"], bounds["max"]
    scene = bpy.context.scene
    _setup_lighting(preset, bounds)
    # character marker (2 wide, 5.5 tall, 1 deep) for scale, beside the asset
    _box((2, 1, 5.5), (hi[0] + 2.0, (lo[1] + hi[1]) / 2, lo[2] + 2.75), _plain("Marker", "#808080", 0.8))

    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    scene.collection.objects.link(cam)
    target = bpy.data.objects.new("Target", None)
    scene.collection.objects.link(target)
    c = cam.constraints.new("TRACK_TO")
    c.target, c.track_axis, c.up_axis = target, "TRACK_NEGATIVE_Z", "UP_Y"
    scene.camera = cam

    scene.render.engine = "CYCLES"
    executor.use_gpu()
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"

    paths = []
    for name, loc, tgt, lens in shots:
        cam.location = Vector(loc)
        target.location = Vector(tgt)
        cam.data.lens = lens
        path = os.path.join(out_dir, "preview_%s.png" % name)
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        paths.append(path)
    return paths
