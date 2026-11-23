from rbxasset.builders import rules
from rbxasset.builders.vocab import ParamDef, Vocab

_N = lambda d, doc="": ParamDef("number", default=d, doc=doc)  # noqa: E731


def validate(p, budgets):
    rules.num(p, "width", 30.0, 80.0)
    rules.num(p, "depth", 22.0, 50.0)
    rules.whole(p, "floors", 3, 8)
    rules.num(p, "floor_height", 9.0, 13.0)
    rules.whole(p, "bays", 4, 10)
    if p["bays"] * 5.6 > p["width"]:
        raise ValueError("%d bays do not fit in width %r" % (p["bays"], p["width"]))


VOCAB = Vocab(
    params={
        "width": _N(52.0),
        "depth": _N(30.0),
        "floors": ParamDef("int", default=5),
        "floor_height": _N(11.0),
        "bays": ParamDef("int", default=8),
        "fire_escape": ParamDef("bool", default=True),
        "water_tank": ParamDef("bool", default=True),
        "street": ParamDef("bool", default=True),
    },
    part_tags=("base", "wall", "wall_b", "trim", "sash", "glass", "door", "soot", "iron", "groove", "wood",
               "roof", "ground", "curb", "road"),
    tiled_tags=frozenset({"base", "wall", "wall_b", "soot", "roof", "ground", "road"}),
    big_tags=frozenset({"wall", "trim", "iron"}),
    no_collide_tags=frozenset({"trim", "sash", "iron", "glass", "groove"}),
    validate=validate,
    makes=("warehouse", "loft building", "factory building", "industrial building", "brick warehouse", "factory"),
    not_for=("house", "church", "skyscraper"),
)
