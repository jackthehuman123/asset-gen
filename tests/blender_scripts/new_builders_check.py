"""Runs inside Blender: checks for the generic builders, selected by the first arg after '--'."""
import importlib
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

from rbxasset.builders import REGISTRY, load_vocab  # noqa: E402

MAX_TRIS = 20000
NOCENTER = {"lamppost"}
OPTIONAL = {"table": {"apron", "stretchers"}, "chair": {"back", "arms"}, "shelf": {"back"},
            "lamppost": {"arm"}, "crate": {"lid"}, "barrel": {"lid"}, "stairs": {"rail"}}


def check(cond, msg):
    if not cond:
        print("FAIL:", msg)
        sys.exit(1)


def clear_scene():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)


def defaults(name):
    return {k: d.default for k, d in load_vocab(name).params.items()}


def build(name, **over):
    clear_scene()
    p = dict(defaults(name), **over)
    load_vocab(name).validate(p, {})
    mod = importlib.import_module(REGISTRY[name] + ".build")
    return p, mod.build(p, random.Random(1))


def verts(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    out = []
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        out.extend(ev.matrix_world @ v.co for v in me.vertices)
        ev.to_mesh_clear()
    return out


def bbox(res, tags=None):
    objs = [o for t, os_ in res.parts.items() if tags is None or t in tags for o in os_]
    vs = verts(objs)
    xs, ys, zs = [v.x for v in vs], [v.y for v in vs], [v.z for v in vs]
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)


def tris(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    n = 0
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        n += sum(len(p.vertices) - 2 for p in me.polygons)
        ev.to_mesh_clear()
    return n


def t_generic(name):
    _, res = build(name)
    vocab = load_vocab(name)
    check(set(res.parts) == set(vocab.part_tags), sorted(res.parts))
    for tag in vocab.part_tags:
        if tag not in OPTIONAL.get(name, ()):
            check(res.parts[tag], "%s: tag %s is empty" % (name, tag))
    x0, x1, y0, y1, z0, z1 = bbox(res)
    check(abs(z0) <= 0.02, (name, "ground", z0))
    if name not in NOCENTER:
        check(abs(x0 + x1) <= 0.05, (name, "x centred", x0, x1))
    for tag, objs in res.parts.items():
        check(tris(objs) < MAX_TRIS, (name, tag, "over budget"))
    check(res.shots and res.shots[0][0] == "wide", [s[0] for s in res.shots])
    for sname, loc, tgt, lens in res.shots:
        check(len(loc) == 3 and len(tgt) == 3 and lens > 0 and Vector(loc) != Vector(tgt), sname)
    check({"W", "H"} <= set(res.ctx), res.ctx)


SPECIFIC = {}


def specific(name):
    def deco(fn):
        SPECIFIC[name] = fn
        return fn
    return deco


@specific("table")
def _table():
    _, res = build("table", height=3.0)
    check(abs(bbox(res)[5] - 3.0) <= 0.02, "table top equals height")
    _, res = build("table", leg_shape="round", apron_height=0.0, stretchers=False)
    check(not res.parts["apron"] and not res.parts["stretchers"], "optional tags empty")


@specific("chair")
def _chair():
    _, res = build("chair", back_style="none")
    check(not res.parts["back"], "stool has no back")
    _, res = build("chair", arms=True, back_style="solid")
    check(res.parts["arms"] and res.parts["back"], "arms and back present")
    _, res = build("chair", seat_width=6.0, seat_height=1.4)
    check(abs(bbox(res, {"seat"})[5] - 1.4) <= 0.02, "seat top equals seat_height")


@specific("shelf")
def _shelf():
    _, res = build("shelf", shelf_count=3)
    check(len(res.parts["shelves"]) == 4, len(res.parts["shelves"]))
    _, res = build("shelf", shelf_count=1, back_panel=False, height=3.0)
    check(len(res.parts["shelves"]) == 2 and not res.parts["back"], "min shelf, no back")


@specific("lamppost")
def _lamppost():
    for style in ("lantern", "globe"):
        _, res = build("lamppost", height=10.0, head_style=style)
        check(abs(bbox(res)[5] - 10.0) <= 0.05, (style, bbox(res)[5]))
    _, res = build("lamppost", arm_length=0.0)
    check(not res.parts["arm"], "no arm")
    check(abs(sum(bbox(res)[0:2])) <= 0.05, "head on top is centred")


@specific("fence")
def _fence():
    _, res = build("fence", length=8.0, post_size=0.3)
    x0, x1 = bbox(res)[0:2]
    check(abs((x1 - x0) - 8.3) <= 0.1, ("fence extent", x1 - x0))
    _, res = build("fence", picket_style="pointed", rail_count=3)
    check(len(res.parts["rails"]) == 3, "three rails")


@specific("crate")
def _crate():
    _, res = build("crate", lid=False)
    check(not res.parts["lid"], "no lid")
    _, res = build("crate", board_count=2, height=1.0)
    check(abs(bbox(res)[5] - 1.1) <= 0.03, ("height plus lid", bbox(res)[5]))


@specific("barrel")
def _barrel():
    _, res = build("barrel", open_top=True)
    check(not res.parts["lid"], "open barrel has no lid")
    _, res = build("barrel", hoop_count=5, height=3.0)
    check(len(res.parts["hoops"]) == 5, "hoop count")
    check(abs(bbox(res)[5] - 3.0) <= 0.03, ("barrel height", bbox(res)[5]))


@specific("stairs")
def _stairs():
    _, res = build("stairs", steps=1)
    check(len(res.parts["treads"]) == 1, "one step")
    _, res = build("stairs", steps=8, rise=0.5)
    check(len(res.parts["treads"]) == 8 and abs(bbox(res)[5] - 4.0) <= 0.02, bbox(res)[5])
    _, res = build("stairs", handrail=True, risers=False, stringers=False)
    check(res.parts["rail"] and not res.parts["risers"], "rail on, risers off")


if __name__ == "__main__":
    which = sys.argv[sys.argv.index("--") + 1]
    kind, name = which.split(":", 1)
    if kind == "generic":
        t_generic(name)
    else:
        SPECIFIC[name]()
    print("OK", which)
