"""Executor: join tagged parts, enforce triangle budget, bake PBR maps, export FBX.
Runs inside Blender."""
import math
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

import bpy

from . import finishes, tiling


class BudgetError(Exception):
    pass


@dataclass
class MeshInfo:
    obj: Any
    name: str
    tag: str
    finish: str
    tris: int
    tiled: bool
    metal: bool
    collide: bool
    maps: Dict[str, str] = field(default_factory=dict)
    big: bool = False
    # procedural material handles used by the bake
    mat: Any = None
    sockets: Dict[str, Any] = field(default_factory=dict)
    bsdf: Any = None
    out: Any = None


def activate(o):
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o


def tag_grain(o):
    """Per-vertex one-hot 'grain' color attribute along the part's longest side."""
    d = o.dimensions
    axis = max(range(3), key=lambda i: d[i])
    attr = o.data.color_attributes.new(name="grain", type="FLOAT_COLOR", domain="POINT")
    col = [0.0, 0.0, 0.0, 1.0]
    col[axis] = 1.0
    for item in attr.data:
        item.color = col


def use_gpu():
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        devs = [d for d in prefs.devices if d.type == "METAL"]
        for d in prefs.devices:
            d.use = d.type == "METAL"
        if devs:
            bpy.context.scene.cycles.device = "GPU"
            return True
    except Exception as e:  # noqa
        print("[executor] GPU unavailable:", e)
    bpy.context.scene.cycles.device = "CPU"
    return False


def join_parts(parts, spec, vocab_sets, style, ctx, prefix) -> List[MeshInfo]:
    for objs in parts.values():
        for o in objs:
            tag_grain(o)
    max_tris = style["budgets"]["max_tris_per_mesh"]
    meshes = []
    for tag, objs in parts.items():
        if not objs:
            continue
        fin = spec["parts"][tag]
        for o in objs:
            if o.modifiers:
                activate(o)
                for mod in list(o.modifiers):
                    bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.object.join()
        o = bpy.context.active_object
        o.name = o.data.name = f"{prefix}_{tag}"
        bpy.context.scene.cursor.location = (0, 0, 0)
        bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
        tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
        if tris > max_tris:
            raise BudgetError(f"{o.name}: {tris} triangles > {max_tris}")
        tiled = tag in vocab_sets.get("tiled_tags", [])
        if tiled:
            tiling.tile_uvs(o, style["studs_per_tile"], use_grain=spec["finishes"][fin]["type"] == "wood")
        else:
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.01)
            bpy.ops.object.mode_set(mode="OBJECT")
        f = spec["finishes"][fin]
        fn = finishes.make_finish(f"{tag}_{fin}_proc", f, spec.get("wear", {}), ctx,
                                  tile=style["studs_per_tile"] if tiled else None)
        o.data.materials.clear()
        o.data.materials.append(fn.mat)
        meshes.append(MeshInfo(
            obj=o, name=o.name, tag=tag, finish=fin, tris=tris, tiled=tiled,
            metal=f["type"] == "metal", collide=tag not in vocab_sets.get("no_collide_tags", []),
            big=tag in vocab_sets.get("big_tags", []),
            mat=fn.mat, sockets=fn.sockets, bsdf=fn.bsdf, out=fn.out))
    return meshes


def bake_meshes(meshes, tex_dir, tiles_dir, spec, style, samples=32) -> float:
    t0 = time.time()
    b = style["budgets"]
    def res_of(me):
        return b["texture_big"] if me.big else b["texture_small"]

    # tiled meshes: one shared tile per finish (largest resolution requested)
    tile_res: Dict[str, int] = {}
    for me in meshes:
        if me.tiled:
            tile_res[me.finish] = max(tile_res.get(me.finish, 0), res_of(me))
    tile_maps = {fin: tiling.bake_tile(fin, spec["finishes"][fin], spec.get("wear", {}),
                                       style["studs_per_tile"], res, tiles_dir)
                 for fin, res in tile_res.items()}
    for me in meshes:
        if me.tiled:
            me.maps = dict(tile_maps[me.finish])

    # bake_tile changes render settings, so (re)apply ours afterwards
    os.makedirs(tex_dir, exist_ok=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    use_gpu()
    sc.cycles.samples = samples
    sc.cycles.use_denoising = False
    sc.render.bake.use_selected_to_active = False
    sc.render.bake.margin = 6
    for me in meshes:
        if me.tiled:
            continue
        o, N, L = me.obj, me.mat.node_tree.nodes, me.mat.node_tree.links
        activate(o)
        res = res_of(me)
        kinds = ["color", "roughness", "normal"] + (["metalness"] if me.metal else [])
        for kind in kinds:
            img = bpy.data.images.new(f"{o.name}_{kind}", res, res, alpha=False)
            if kind != "color":
                img.colorspace_settings.name = "Non-Color"
            tex = N.new("ShaderNodeTexImage")
            tex.image = img
            for n in N:
                n.select = False
            tex.select = True
            N.active = tex
            if kind == "normal":
                L.new(me.bsdf.outputs["BSDF"], me.out.inputs["Surface"])
                bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT")
            else:
                em = N.new("ShaderNodeEmission")
                L.new(me.sockets[kind], em.inputs["Color"])
                L.new(em.outputs["Emission"], me.out.inputs["Surface"])
                bpy.ops.object.bake(type="EMIT")
                N.remove(em)
            path = os.path.join(tex_dir, f"{o.name}_{kind}.png")
            img.filepath_raw = path
            img.file_format = "PNG"
            img.save()
            img.filepath = path
            me.maps[kind] = path
            N.remove(tex)
        L.new(me.bsdf.outputs["BSDF"], me.out.inputs["Surface"])
    return time.time() - t0


def swap_to_baked(meshes) -> None:
    for me in meshes:
        o = me.obj
        mt = bpy.data.materials.new(f"{o.name}_baked")
        mt.use_nodes = True
        N, L = mt.node_tree.nodes, mt.node_tree.links
        bsdf = N["Principled BSDF"]

        def tex(kind):
            t = N.new("ShaderNodeTexImage")
            t.image = bpy.data.images.load(me.maps[kind], check_existing=True)
            if kind != "color":
                t.image.colorspace_settings.name = "Non-Color"
            return t

        L.new(tex("color").outputs["Color"], bsdf.inputs["Base Color"])
        L.new(tex("roughness").outputs["Color"], bsdf.inputs["Roughness"])
        if "metalness" in me.maps:
            L.new(tex("metalness").outputs["Color"], bsdf.inputs["Metallic"])
        else:
            bsdf.inputs["Metallic"].default_value = 0.0
        nm = N.new("ShaderNodeNormalMap")
        L.new(tex("normal").outputs["Color"], nm.inputs["Color"])
        L.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
        o.data.materials.clear()
        o.data.materials.append(mt)


def export_fbx(meshes, path) -> None:
    """Export with baked maps embedded, so Studio's File > Import 3D brings in
    every SurfaceAppearance map in one step (creator-verified 2026-11-22)."""
    bpy.ops.object.select_all(action="DESELECT")
    for me in meshes:
        me.obj.select_set(True)
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_UNITS", axis_forward="-Z", axis_up="Y",
        mesh_smooth_type="FACE", path_mode="COPY", embed_textures=True)
