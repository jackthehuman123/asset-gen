"""Runs inside Blender: executor checks, selected by the first arg after '--'."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import bpy  # noqa: E402

from rbxasset.blender import executor  # noqa: E402

WOOD = {"type": "wood", "base": "#8a5a2b", "grain": "#4a2c10"}
METAL = {"type": "metal", "color": "#9a9a9a"}
STYLE = {
    "studs_per_tile": 4.0,
    "budgets": {"max_tris_per_mesh": 20000, "texture_big": 1024, "texture_small": 512},
    "lighting": {},
}


def check(cond, msg):
    if not cond:
        print("FAIL:", msg)
        sys.exit(1)


def spec(parts, **fin):
    return {"parts": parts, "finishes": fin, "wear": {}}


def vocab(tiled=(), big=(), no_collide=()):
    return {
        "tiled_tags": list(tiled),
        "big_tags": list(big),
        "no_collide_tags": list(no_collide),
    }


def cube(loc=(0, 0, 0), size=1.0):
    bpy.ops.mesh.primitive_cube_add(size=size, location=loc)
    return bpy.context.active_object


def t_join():
    parts = {"a": [cube(), cube((3, 0, 0))], "b": [cube((0, 3, 0))]}
    sp = spec({"a": "wood", "b": "metal"}, wood=WOOD, metal=METAL)
    ms = executor.join_parts(
        parts, sp, vocab(no_collide=["b"]), STYLE, {"W": 4, "H": 4}, "T"
    )
    check([m.name for m in ms] == ["T_a", "T_b"], [m.name for m in ms])
    check([m.tris for m in ms] == [24, 12], [m.tris for m in ms])
    check(ms[0].finish == "wood" and not ms[0].metal and ms[0].collide, "a info")
    check(ms[1].metal and not ms[1].collide, "b info")
    check(
        bpy.data.objects["T_a"].data.attributes.get("grain") is not None, "grain attr"
    )


def t_budget():
    bpy.ops.mesh.primitive_grid_add(
        x_subdivisions=102, y_subdivisions=102
    )  # 20808 tris
    o = bpy.context.active_object
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.quads_convert_to_tris()
    bpy.ops.object.mode_set(mode="OBJECT")
    n = len(o.data.polygons)
    check(n > 20000, n)
    try:
        executor.join_parts(
            {"big": [o]}, spec({"big": "wood"}, wood=WOOD), vocab(), STYLE, {}, "T"
        )
    except executor.BudgetError as e:
        check(str(e) == f"T_big: {n} triangles > 20000", str(e))
        return
    check(False, "no BudgetError")


def t_bake():
    parts = {"big": [cube()], "small": [cube((3, 0, 0))], "met": [cube((6, 0, 0))]}
    sp = spec({"big": "wood", "small": "wood", "met": "metal"}, wood=WOOD, metal=METAL)
    ms = executor.join_parts(
        parts, sp, vocab(big=["big"]), STYLE, {"W": 4, "H": 4}, "T"
    )
    tmp = tempfile.mkdtemp()
    secs = executor.bake_meshes(ms, tmp, tmp + "/tiles", sp, STYLE, samples=1)
    check(secs > 0, "seconds")
    by = {m.tag: m for m in ms}

    def size(m, k):
        img = bpy.data.images.load(m.maps[k], check_existing=False)
        return tuple(img.size)

    check(size(by["big"], "color") == (1024, 1024), size(by["big"], "color"))
    check(size(by["small"], "color") == (512, 512), size(by["small"], "color"))
    check(
        "metalness" in by["met"].maps and Path(by["met"].maps["metalness"]).exists(),
        "metal map",
    )
    check("metalness" not in by["big"].maps, "wood has no metalness")
    check({"color", "roughness", "normal"} <= set(by["big"].maps), "kinds")
    executor.swap_to_baked(ms)
    check(all(m.obj.data.materials[0].name.endswith("_baked") for m in ms), "swap")


def t_tiled():
    parts = {"x": [cube(size=8)], "y": [cube((10, 0, 0), size=8)]}
    sp = spec({"x": "wood", "y": "wood"}, wood=WOOD)
    ms = executor.join_parts(
        parts, sp, vocab(tiled=["x", "y"]), STYLE, {"W": 4, "H": 4}, "T"
    )
    check(all(m.tiled for m in ms), "tiled flag")
    # color-form grain through the real join path: U must follow grain scale
    uv = ms[0].obj.data.uv_layers["UVMap"].data
    us = [uv[i].uv[0] for i in range(len(uv))]
    check(max(us) - min(us) >= 1.9, "tile uv extent")  # 8 studs / 4 per tile = 2
    tmp = tempfile.mkdtemp()
    executor.bake_meshes(ms, tmp + "/tex", tmp + "/tiles", sp, STYLE, samples=1)
    check(ms[0].maps["color"] == ms[1].maps["color"], "shared color")
    check(
        str(Path(ms[0].maps["color"]).parent) == str(Path(tmp, "tiles")),
        ms[0].maps["color"],
    )
    check(Path(ms[0].maps["color"]).exists(), "exists")


def t_fbx():
    parts = {"a": [cube()], "b": [cube((3, 0, 0), size=2)]}
    sp = spec({"a": "wood", "b": "metal"}, wood=WOOD, metal=METAL)
    ms = executor.join_parts(parts, sp, vocab(), STYLE, {"W": 4, "H": 4}, "T")
    tmp = tempfile.mkdtemp()
    executor.bake_meshes(ms, tmp, tmp + "/tiles", sp, STYLE, samples=1)
    executor.swap_to_baked(ms)
    path = tmp + "/out.fbx"
    executor.export_fbx(ms, path)
    check(Path(path).exists() and Path(path).stat().st_size > 0, "fbx missing")
    want = {m.name: m.tris for m in ms}
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    got = {
        o.name.split(".")[0]: sum(len(p.vertices) - 2 for p in o.data.polygons)
        for o in bpy.data.objects
        if o.type == "MESH"
    }
    check(got == want, f"{got} != {want}")


globals()["t_" + sys.argv[sys.argv.index("--") + 1]]()
print("executor_check OK")
