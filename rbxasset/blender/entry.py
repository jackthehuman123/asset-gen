"""Blender entry point: blender -b --python entry.py -- job.json

Job: {"mode": "build"|"sample", "spec": ResolvedSpec dict,
      "style": {"studs_per_tile", "budgets", "lighting"},
      "vocab": {"tiled_tags", "big_tags", "no_collide_tags"},
      "asset", "out_dir", "tiles_dir", "manifest_path"}

Optional render knobs live in style.budgets: "preview_samples" and "preview_res" [w, h].

Manifest (written to manifest_path). All file paths are ABSOLUTE; coordinates are
Blender coordinates (Z up, studs), converted to Roblox in the upload step.
  {"asset", "mode", "fbx": path|null, "bounds": {"min": [x,y,z], "max": [x,y,z]},
   "meshes": [{"name","tag","finish","tris","tiled","metal","collide","maps": {kind: path}}],
   "decals": [{"name","image","on","position","normal","size","opacity"}],
   "previews": [path], "bake_seconds": float}
The decal never goes into the FBX; the manifest is its only record.
"""
import importlib
import json
import math
import os
import random
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

from rbxasset.blender import decals, executor, preview  # noqa: E402
from rbxasset.builders import REGISTRY  # noqa: E402

DECAL_RES = 256


def _bounds(meshes):
    pts = [o.matrix_world @ Vector(c) for o in (m.obj for m in meshes) for c in o.bound_box]
    return {"min": [min(p[i] for p in pts) for i in range(3)],
            "max": [max(p[i] for p in pts) for i in range(3)]}


def _render_decals(spec, out_dir):
    """Render decal images; add preview-only planes. Returns manifest entries."""
    entries = []
    for i, d in enumerate(spec.get("decals", [])):
        path = os.path.abspath(os.path.join(out_dir, "textures", "decal_%d.png" % i))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        decals.render_decal(d["kind"], d["color"], spec["seed"] + i, DECAL_RES, path)
        opacity = float(d.get("opacity", 1.0))
        name = "decal_%d_%s" % (i, d["kind"])
        entries.append({"name": name, "image": path, "on": d["on"],
                        "position": list(d["position"]), "normal": list(d["normal"]),
                        "size": list(d["size"]), "opacity": opacity})
    return entries


def _add_decal_planes(entries):
    for e in entries:
        n = Vector(e["normal"]).normalized()
        bpy.ops.mesh.primitive_plane_add(size=1, location=Vector(e["position"]) + n * 0.01)
        o = bpy.context.active_object
        o.name = e["name"]
        o.scale = (e["size"][0], e["size"][1], 1)
        o.rotation_euler = n.to_track_quat("Z", "Y").to_euler()
        mt = bpy.data.materials.new(e["name"])
        mt.use_nodes = True
        N, L = mt.node_tree.nodes, mt.node_tree.links
        b = N["Principled BSDF"]
        t = N.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(e["image"], check_existing=True)
        t.image.alpha_mode = "STRAIGHT"
        mul = N.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = e["opacity"]
        L.new(t.outputs["Color"], b.inputs["Base Color"])
        L.new(t.outputs["Alpha"], mul.inputs[0])
        L.new(mul.outputs["Value"], b.inputs["Alpha"])
        b.inputs["Roughness"].default_value = 0.4
        o.data.materials.append(mt)


def run(job):
    spec, style, vocab = job["spec"], job["style"], job["vocab"]
    out_dir, mode = job["out_dir"], job["mode"]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"

    mod = importlib.import_module(REGISTRY[spec["builder"]] + ".build")
    res = mod.build(spec["params"], random.Random(spec["seed"]))
    prefix = job["asset"].split("/")[-1]
    meshes = executor.join_parts(res.parts, spec, vocab, style, res.ctx, prefix)

    fbx, bake_s = None, 0.0
    if mode == "build":
        bake_s = executor.bake_meshes(meshes, os.path.join(out_dir, "textures"),
                                      job["tiles_dir"], spec, style)
        executor.swap_to_baked(meshes)
        fbx = os.path.join(out_dir, "asset.fbx")
        executor.export_fbx(meshes, fbx)
    bounds = _bounds(meshes)
    decal_entries = _render_decals(spec, out_dir)
    _add_decal_planes(decal_entries)

    b = style["budgets"]
    if mode == "sample":
        samples, size = 24, (800, 600)
    else:
        samples, size = int(b.get("preview_samples", 64)), tuple(b.get("preview_res", (1200, 900)))
    preset = style.get("lighting", {}).get("preset", "overcast_exterior")
    previews = preview.render_shots(res.shots, preset, os.path.join(out_dir, "previews"),
                                    samples, size, bounds)

    manifest = {
        "asset": job["asset"], "mode": mode, "fbx": fbx, "bounds": bounds,
        "meshes": [{"name": m.name, "tag": m.tag, "finish": m.finish, "tris": m.tris,
                    "tiled": m.tiled, "metal": m.metal, "collide": m.collide,
                    "maps": {k: os.path.abspath(v) for k, v in m.maps.items()}} for m in meshes],
        "decals": decal_entries,
        "previews": [os.path.abspath(p) for p in previews],
        "bake_seconds": bake_s,
    }
    os.makedirs(os.path.dirname(job["manifest_path"]), exist_ok=True)
    with open(job["manifest_path"], "w") as f:
        json.dump(manifest, f, indent=2)


def main():
    job_path = sys.argv[sys.argv.index("--") + 1]
    with open(job_path) as f:
        job = json.load(f)
    try:
        run(job)
    except Exception:
        traceback.print_exc()
        sys.exit(1)


main()
