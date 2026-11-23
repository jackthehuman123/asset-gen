from rbxasset.builders import rules
from rbxasset.builders.vocab import ParamDef, Vocab

_N = lambda d, doc="": ParamDef("number", default=d, doc=doc)  # noqa: E731


def validate(p, budgets):
    rules.num(p, "width", 12.0, 22.0)
    rules.num(p, "depth", 24.0, 60.0)
    rules.whole(p, "floors", 3, 5)
    rules.num(p, "floor_height", 8.5, 13.0)
    rules.num(p, "basement_height", 3.0, 6.5)
    rules.whole(p, "bays", 2, 4)
    if p["bays"] * 4.6 > p["width"]:
        raise ValueError("%d bays do not fit in width %r" % (p["bays"], p["width"]))


VOCAB = Vocab(
    params={
        "width": _N(15.0, "party wall to party wall, about 16 ft"),
        "depth": _N(38.0),
        "floors": ParamDef("int", default=4, doc="storeys above the raised basement (3-5)"),
        "floor_height": _N(10.5),
        "basement_height": _N(4.5),
        "bays": ParamDef("int", default=3, doc="window bays across the front; the door takes the first"),
        "stoop": ParamDef("bool", default=True),
        "cornice": ParamDef("bool", default=True),
        "street": ParamDef("bool", default=True, doc="sidewalk, curb and road in front"),
    },
    part_tags=("base", "wall", "wall_b", "brick", "trim", "sash", "glass", "door", "soot", "iron", "groove",
               "roof", "ground", "curb", "road"),
    tiled_tags=frozenset({"base", "wall", "wall_b", "brick", "soot", "roof", "ground", "road"}),
    big_tags=frozenset({"wall", "base", "brick", "trim"}),
    no_collide_tags=frozenset({"trim", "sash", "iron", "groove", "glass"}),
    validate=validate,
    makes=("brownstone", "brownstone townhouse", "new york townhouse"),
    not_for=("detached house", "skyscraper", "castle"),
)
