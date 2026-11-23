"""Seamless per-finish tiles and tile-aware UVs. Runs inside Blender."""

import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Vector

from . import finishes

TILE_RECIPE = 3  # bump when finishes.py changes what a tile looks like

# (kind, socket key, bake colorspace)
_KINDS = (
    ("color", "color", "sRGB"),
    ("roughness", "roughness", "Non-Color"),
    ("metalness", "metalness", "Non-Color"),
)


def _hash(finish, wear, studs, res):
    blob = json.dumps([TILE_RECIPE, finish, wear, studs, res], sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def _bake_image(img_name, res, cs, bake_type, tree, tex_img):
    img = bpy.data.images.new(img_name, res, res, float_buffer=False)
    img.colorspace_settings.name = cs
    tex_img.image = img
    tree.nodes.active = tex_img
    bpy.ops.object.bake(
        type=bake_type, margin=0, use_clear=True, normal_space="TANGENT"
    )
    return img


def bake_tile(finish_name, finish, wear, studs, res, out_dir):
    """Bake color/roughness/(metalness)/normal PNGs for one finish; cached by hash."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    kinds = (
        ["color", "roughness"]
        + (["metalness"] if finish.get("type") == "metal" else [])
        + ["normal"]
    )
    paths = {k: str(out / f"{finish_name}_{k}.png") for k in kinds}
    hfile = out / f"{finish_name}.hash"
    h = _hash(finish, wear, studs, res)
    if (
        hfile.exists()
        and hfile.read_text() == h
        and all(Path(p).exists() for p in paths.values())
    ):
        return paths

    bpy.ops.mesh.primitive_plane_add(size=1)
    plane = bpy.context.active_object
    fn = finishes.make_finish(
        finish_name, finish, wear, {"W": studs, "H": studs}, tile=studs
    )
    plane.data.materials.append(fn.mat)
    tree = fn.mat.node_tree
    tex_img = tree.nodes.new("ShaderNodeTexImage")
    emit = tree.nodes.new("ShaderNodeEmission")
    orig_link = fn.out.inputs["Surface"].links[0]
    surf_from = orig_link.from_socket

    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 4
    sc.cycles.use_denoising = False
    sc.render.bake.use_selected_to_active = False

    def save(kind, img):
        img.filepath_raw = paths[kind]
        img.file_format = "PNG"
        img.save()

    for kind, key, cs in _KINDS:
        if kind not in paths:
            continue
        tree.links.new(fn.sockets[key], emit.inputs["Color"])
        tree.links.new(emit.outputs["Emission"], fn.out.inputs["Surface"])
        save(kind, _bake_image(f"{finish_name}_{kind}", res, cs, "EMIT", tree, tex_img))

    tree.links.new(surf_from, fn.out.inputs["Surface"])
    save(
        "normal",
        _bake_image(f"{finish_name}_normal", res, "Non-Color", "NORMAL", tree, tex_img),
    )

    bpy.data.objects.remove(plane)
    hfile.write_text(h)
    return paths


def _grain_axis(obj):
    """Axis index (0/1/2) from the 'grain' attribute: int value or one-hot color, else None."""
    a = obj.data.attributes.get("grain") if obj.data else None
    if a is None or len(a.data) == 0:
        return None
    d = a.data[0]
    if a.data_type == "INT":
        return int(d.value)
    c = d.color if hasattr(d, "color") else d.vector
    return max(range(3), key=lambda i: abs(c[i]))


def tile_uvs(obj, studs, use_grain=True):
    """Planar UVs = world coords / studs on the two axes perpendicular to each face's
    dominant normal axis; U follows the grain axis when it lies in that plane (wood only:
    brick courses and siding boards must stay horizontal, whatever the part's longest side)."""
    mesh = obj.data
    uv = mesh.uv_layers.get("UVMap") or mesh.uv_layers.new(name="UVMap")
    grain = _grain_axis(obj) if use_grain else None
    mw = obj.matrix_world
    for poly in mesh.polygons:
        n = mw.to_3x3() @ Vector(poly.normal)
        dom = max(range(3), key=lambda i: abs(n[i]))
        u_ax, v_ax = [i for i in range(3) if i != dom]
        if grain is not None and grain != dom:
            u_ax = grain
            v_ax = next(i for i in range(3) if i not in (dom, grain))
        for li in poly.loop_indices:
            p = mw @ mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv = (p[u_ax] / studs, p[v_ax] / studs)
