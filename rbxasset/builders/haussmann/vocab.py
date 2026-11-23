from rbxasset.builders import rules
from rbxasset.builders.vocab import ParamDef, Vocab

_N = lambda d, doc="": ParamDef("number", default=d, doc=doc)  # noqa: E731


def validate(p, budgets):
    rules.num(p, "width", 28.0, 60.0)
    rules.num(p, "depth", 20.0, 40.0)
    rules.whole(p, "floors", 4, 7)
    rules.num(p, "floor_height", 9.0, 12.0)
    rules.whole(p, "bays", 5, 9)
    if p["bays"] * 4.6 > p["width"]:
        raise ValueError("%d bays do not fit in width %r" % (p["bays"], p["width"]))


VOCAB = Vocab(
    params={
        "width": _N(42.0),
        "depth": _N(28.0),
        "floors": ParamDef("int", default=5, doc="storeys above the ground floor, under the mansard"),
        "floor_height": _N(10.0),
        "bays": ParamDef("int", default=7),
        "balconies": ParamDef("bool", default=True, doc="continuous iron balconies on the 2nd and 5th floors"),
        "street": ParamDef("bool", default=True),
    },
    part_tags=("base", "wall", "wall_b", "trim", "sash", "glass", "door", "soot", "iron", "groove", "roof",
               "ground", "curb", "road"),
    tiled_tags=frozenset({"base", "wall", "wall_b", "soot", "roof", "ground", "road"}),
    big_tags=frozenset({"wall", "trim", "roof"}),
    no_collide_tags=frozenset({"trim", "sash", "iron", "glass", "groove"}),
    validate=validate,
    makes=("haussmann building", "parisian apartment", "paris apartment building", "mansard building",
           "french apartment building"),
    not_for=("house", "skyscraper", "cabin"),
)
