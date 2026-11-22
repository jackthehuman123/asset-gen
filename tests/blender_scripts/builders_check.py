"""Runs inside Blender: builder checks, selected by the first arg after '--'."""
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

from rbxasset.builders import load_vocab  # noqa: E402
from rbxasset.builders.cabinet import build as cabinet_build  # noqa: E402
from rbxasset.builders.house import build as house_build  # noqa: E402
from rbxasset.spec import load_spec  # noqa: E402
from rbxasset.style import load_style  # noqa: E402

FIX = ROOT / "tests" / "fixtures"
STYLE = load_style(FIX / "game_STYLE.md", FIX / "area_STYLE.md")
MAX_TRIS = 20000


def check(cond, msg):
    if not cond:
        print("FAIL:", msg)
        sys.exit(1)


def fixture(name):
    return load_spec(FIX / name, STYLE)


def clear_scene():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)


def build_house(params=None, seed=13):
    sp = fixture("house_spec.json")
    p = dict(sp.params, **(params or {}))
    return p, house_build.build(p, random.Random(seed))


def world_verts(objs):
    """Evaluated (modifiers applied) world-space vertex positions."""
    dg = bpy.context.evaluated_depsgraph_get()
    out = []
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        mw = ev.matrix_world
        out.extend(mw @ v.co for v in me.vertices)
        ev.to_mesh_clear()
    return out


def joined_tris(objs):
    for o in objs:
        if o.modifiers:
            bpy.ops.object.select_all(action="DESELECT")
            o.select_set(True)
            bpy.context.view_layer.objects.active = o
            for mod in list(o.modifiers):
                bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def t_house_deterministic():
    _, a = build_house()
    counts_a = {t: len(v) for t, v in a.parts.items()}
    clear_scene()
    _, b = build_house()
    counts_b = {t: len(v) for t, v in b.parts.items()}
    check(counts_a == counts_b, (counts_a, counts_b))
    clear_scene()
    _, c = build_house(seed=29)
    counts_c = {t: len(v) for t, v in c.parts.items()}
    check(counts_c != counts_a, "seed has no effect on damage")


def t_house_budget():
    _, res = build_house()
    vocab = load_vocab("house")
    check(set(res.parts) == set(vocab.part_tags), sorted(res.parts))
    tris = {}
    for tag in vocab.part_tags:
        check(len(res.parts[tag]) >= 1, "no parts for tag %s" % tag)
        tris[tag] = joined_tris(res.parts[tag])
    print("TRIS", tris)
    over = {t: n for t, n in tris.items() if n >= MAX_TRIS}
    check(not over, over)


def t_house_pan_cover():
    _, res = build_house()
    for tag in ("tiles_front", "tiles_back"):
        names = [o.name for o in res.parts[tag]]
        pans = sum(n.startswith("pan_") for n in names)
        covers = sum(n.startswith("cover_") for n in names)
        print(tag, "pans", pans, "covers", covers)
        check(pans > 0 and covers > 0, (tag, pans, covers))
        check(pans + covers == len(names), "%s has non pan/cover objects" % tag)
        check(abs(pans - covers) <= 0.15 * max(pans, covers), (tag, pans, covers))


def t_house_sag():
    p, res = build_house()
    W, sag = p["width"], p["roof_sag"]
    check(sag > 0, "fixture sag")
    vs = world_verts(res.parts["ridge"])
    mid = max(v.z for v in vs if abs(v.x) < 1.0)
    ends = [max(v.z for v in vs if abs(v.x - s * W / 2) < 1.0) for s in (-1, 1)]
    print("ridge z mid", mid, "ends", ends)
    for e in ends:
        check(e - mid >= 0.5 * sag, ("sag", mid, ends))
    # control: no sag -> flat ridge (unsagged pieces aren't bisected, so probe by ray)
    clear_scene()
    p, res = build_house({"roof_sag": 0.0})
    ridge = {o.name for o in res.parts["ridge"]}
    dg = bpy.context.evaluated_depsgraph_get()
    tops = []
    for x in (0.0, -W / 2, W / 2):
        ok, loc, _n, _i, obj, _m = bpy.context.scene.ray_cast(dg, Vector((x, 0, 100)), Vector((0, 0, -1)))
        check(ok and obj.name in ridge, ("ray missed ridge", x))
        tops.append(loc.z)
    check(max(tops) - min(tops) < 1e-3, ("flat", tops))


def t_house_openings():
    p, res = build_house()
    tag_of = {o.name: t for t, objs in res.parts.items() for o in objs}
    W, D, F = p["width"], p["depth"], p["floor_height"]
    bays = p["facades"]["front"]
    bw = W / len(bays)
    z = F + p["sill_height"] + 1.0
    dg = bpy.context.evaluated_depsgraph_get()
    windows = [i for i, k in enumerate(bays) if k == "window"]
    check(windows, "fixture has no front windows")
    for i in windows:
        x = -W / 2 + (i + 0.5) * bw
        origin = Vector((x, -D / 2 - 30, z))
        hits = []
        while True:
            ok, loc, _n, _i, obj, _m = bpy.context.scene.ray_cast(dg, origin, Vector((0, 1, 0)))
            if not ok or loc.y >= 0:
                break
            hits.append((tag_of.get(obj.name, "?"), round(loc.y, 2)))
            origin = loc + Vector((0, 1e-3, 0))
        print("bay", i, "hits", hits)
        bad = [h for h in hits if h[0] in ("plaster", "siding")]
        check(not bad, ("bay", i, bad))
        check(not any(h[1] > -D / 2 + 0.5 for h in hits if h[0] == "?"), "unknown objects")


def t_cabinet_dims():
    sp = fixture("cabinet_spec.json")
    p = dict(sp.params, width=5.4, body_height=1.55, leg_height=0.45)
    res = cabinet_build.build(p, random.Random(1))
    vocab = load_vocab("cabinet")
    check(set(res.parts) == set(vocab.part_tags), sorted(res.parts))
    check(all(res.parts[t] for t in vocab.part_tags), "empty tag")
    vs = world_verts([o for objs in res.parts.values() for o in objs])
    xs, ys, zs = [v.x for v in vs], [v.y for v in vs], [v.z for v in vs]
    w, h = max(xs) - min(xs), max(zs) - min(zs)
    print("cabinet w", w, "h", h, "zmin", min(zs))
    check(abs(w - 5.48) <= 0.02, ("width", w))
    check(abs(h - 2.0) <= 0.02, ("height", h))
    check(abs(min(zs)) <= 0.02, ("ground", min(zs)))
    check(abs(max(xs) + min(xs)) <= 0.02, ("x centered", min(xs), max(xs)))
    check(abs(res.ctx["W"] - 5.4) < 1e-6 and abs(res.ctx["H"] - 2.0) < 1e-6, res.ctx)


def _check_shots(shots, names):
    check([s[0] for s in shots] == names, [s[0] for s in shots])
    for name, loc, tgt, lens in shots:
        check(len(loc) == 3 and len(tgt) == 3, name)
        check(all(isinstance(v, (int, float)) for v in (*loc, *tgt, lens)), name)
        check(lens > 0 and Vector(loc) != Vector(tgt), name)


def t_shots():
    _, res = build_house()
    _check_shots(res.shots, ["wide", "front", "close_opening", "roof"])
    check(set(res.ctx) == {"W", "H"}, res.ctx)
    clear_scene()
    sp = fixture("cabinet_spec.json")
    res = cabinet_build.build(dict(sp.params), random.Random(1))
    _check_shots(res.shots, ["wide", "close"])
    check(set(res.ctx) == {"W", "H"}, res.ctx)


TESTS = {
    "house_deterministic": t_house_deterministic,
    "house_budget": t_house_budget,
    "house_pan_cover": t_house_pan_cover,
    "house_sag": t_house_sag,
    "house_openings": t_house_openings,
    "cabinet_dims": t_cabinet_dims,
    "shots": t_shots,
}

if __name__ == "__main__":
    name = sys.argv[sys.argv.index("--") + 1]
    TESTS[name]()
    print("OK", name)
