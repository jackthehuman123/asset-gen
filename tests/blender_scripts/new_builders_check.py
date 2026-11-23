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
NOCENTER = {"lamppost", "victorian", "tudor", "craftsman"}
OPTIONAL = {"warehouse": set(), "table": {"apron", "stretchers"}, "chair": {"back", "arms"}, "shelf": {"back"},
            "lamppost": {"arm"}, "crate": {"lid"}, "barrel": {"lid"}, "stairs": {"rail"}, "art_deco_tower": {"groove"}, "church": {"iron"},
            "colonial_revival": {"shutter"}}


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


@specific("detached_house")
def _detached_house():
    tops = {}
    for form in ("gable", "hip", "gambrel", "saltbox"):
        _, res = build("detached_house", roof_form=form, chimney=False)
        tops[form] = bbox(res)[5]
        check(res.parts["roof"] and not res.parts["chimney"], form)
    check(tops["gambrel"] > tops["gable"] * 0.9, tops)
    _, one = build("detached_house", storeys=1)
    h1 = bbox(one)[5]
    _, two = build("detached_house", storeys=2)
    check(bbox(two)[5] - h1 >= 8.0, "second storey adds height")
    _, res = build("detached_house", porch=False)
    check(len(res.parts["foundation"]) == 1, "no porch means one foundation box")
    _, res = build("detached_house", bays=4, side_windows=0, back_windows=0)
    check(len(res.parts["glazing"]) == 3, ("4 bays minus door, no side/back windows", len(res.parts["glazing"])))


@specific("rowhouse")
def _rowhouse():
    _, res = build("rowhouse", floors=3)
    check(abs(bbox(res)[5] - (3.6 + 3 * 9.5 + 1.3)) <= 0.05, bbox(res)[5])
    _, res = build("rowhouse", stoop=False, cornice=False)
    check(len(res.parts["foundation"]) == 1, "no stoop means one foundation box")
    x0, x1 = bbox(res)[0:2]
    check(abs((x1 - x0) - 14.1) <= 0.1, ("party-wall width", x1 - x0))


@specific("apartment")
def _apartment():
    _, res = build("apartment", floors=4, columns=4, side_columns=2)
    check(len(res.parts["glazing"]) == 4 * (2 * 4 + 2 * 2) - 1, len(res.parts["glazing"]))
    _, res = build("apartment", floors=2, columns=2, side_columns=0)
    check(len(res.parts["glazing"]) == 2 * 4 - 1, len(res.parts["glazing"]))


@specific("cabin")
def _cabin():
    _, a = build("cabin", log_courses=9)
    ha, logs = bbox(a)[5], len(a.parts["logs"])
    _, b = build("cabin", log_courses=12)
    check(logs > 20, logs)
    check(bbox(b)[5] > ha + 1.5, "more courses make it taller")
    _, res = build("cabin", porch=False, chimney=False)
    check(not res.parts["chimney"] and len(res.parts["foundation"]) == 1, "no porch/chimney")


@specific("barn")
def _barn():
    _, res = build("barn", length=40.0, width=22.0)
    x0, x1, y0, y1, z0, z1 = bbox(res)
    check(abs((y1 - y0) - (40.0 + 2 * 1.2)) <= 0.2, ("ridge runs along y", y1 - y0))
    check(x1 - x0 >= 22.0, ("gable end width", x1 - x0))
    _, res = build("barn", loft_door=False)
    check(res.parts["door"], "big doors present")


def _count(res, tag):
    return len(res.parts[tag])


@specific("brownstone")
def _brownstone():
    _, a = build("brownstone", floors=3)
    h3 = bbox(a)[5]
    _, b = build("brownstone", floors=5)
    check(bbox(b)[5] - h3 >= 2 * 10.5 - 0.2, "two more floors add two storeys")
    _, res = build("brownstone", stoop=False, cornice=False, street=False)
    check(not res.parts["ground"] and not res.parts["curb"], "no street means empty ground and curb")


@specific("victorian")
def _victorian():
    _, a = build("victorian")
    ra = _count(a, "roof")
    _, b = build("victorian", turret=False, porch=False)
    check(_count(b, "roof") < ra, "no turret or porch means fewer roof pieces")
    check(len(b.parts["glass"]) > 8, "windows present")


@specific("tudor")
def _tudor():
    _, res = build("tudor")
    check(_count(res, "timber") > 40, ("half-timber overlay", _count(res, "timber")))
    _, flat = build("tudor", jetty=0.0)
    check(len(flat.parts["timber"]) > 20, "timber without jetty")


@specific("craftsman")
def _craftsman():
    _, res = build("craftsman")
    check(_count(res, "trim") > 60, ("rafter tails and beams", _count(res, "trim")))
    check(_count(res, "brick") >= 4, "porch piers")


@specific("colonial_revival")
def _colonial():
    _, a = build("colonial_revival", bays=5)
    ga = _count(a, "glass")
    _, b = build("colonial_revival", bays=7, portico=False)
    check(_count(b, "glass") - ga == 8, ("two more bays add 8 panes", ga, _count(b, "glass")))


@specific("art_deco_tower")
def _deco():
    _, a = build("art_deco_tower", crown=False)
    ha = bbox(a)[5]
    _, b = build("art_deco_tower", crown=True)
    check(bbox(b)[5] > ha + 30, "crown and spire add height")
    _, c = build("art_deco_tower", floors=12, setbacks=1)
    check(bbox(c)[5] < ha, "fewer floors is shorter")


@specific("haussmann")
def _haussmann():
    _, a = build("haussmann", floors=4)
    ha = bbox(a)[5]
    _, b = build("haussmann", floors=6, balconies=False)
    check(bbox(b)[5] > ha + 2 * 10.0 - 0.3, "two more floors")
    check(_count(b, "roof") >= 2 + 2 * 7, "mansard slopes and dormers")


@specific("warehouse")
def _warehouse():
    _, a = build("warehouse")
    ia = _count(a, "iron")
    _, b = build("warehouse", fire_escape=False, water_tank=False)
    check(_count(b, "iron") < ia and not b.parts["wood"], "no fire escape or tank")


@specific("church")
def _church():
    _, a = build("church", bays=5)
    ga = _count(a, "glass")
    _, b = build("church", bays=7, nave_length=70.0)
    check(_count(b, "glass") - ga == 4, ("two more bays add 4 windows", ga, _count(b, "glass")))
    check(bbox(b)[5] > 60, "spire towers over the nave")


@specific("shopfront_block")
def _shops():
    _, res = build("shopfront_block", shops=2)
    check(res.parts["awning"] and res.parts["awning_b"], "two awning colours")
    _, none = build("shopfront_block", awnings=False, fire_escape=False)
    check(not none.parts["awning"] and not none.parts["awning_b"], "no awnings")


if __name__ == "__main__":
    which = sys.argv[sys.argv.index("--") + 1]
    kind, name = which.split(":", 1)
    if kind == "generic":
        t_generic(name)
    else:
        SPECIFIC[name]()
    print("OK", which)
