from rbxasset.builders import rules
from rbxasset.builders.vocab import ParamDef, Vocab

_N = lambda d, doc="": ParamDef("number", default=d, doc=doc)  # noqa: E731


def validate(p, budgets):
    rules.num(p, "width", 30.0, 70.0)
    rules.num(p, "depth", 26.0, 60.0)
    rules.whole(p, "floors", 8, 40)
    rules.num(p, "floor_height", 8.0, 12.0)
    rules.whole(p, "setbacks", 1, 4)
    rules.num(p, "setback_depth", 2.0, 8.0)
    rules.whole(p, "bays", 5, 14)
    if (p["width"] - 2 * p["setbacks"] * p["setback_depth"] < 14) or (p["depth"] - 2 * p["setbacks"] * p["setback_depth"] < 12):
        raise ValueError("setbacks leave too small a top tier; reduce setbacks or setback_depth")


VOCAB = Vocab(
    params={
        "width": _N(46.0),
        "depth": _N(38.0),
        "floors": ParamDef("int", default=24, doc="storeys above the ground floor"),
        "floor_height": _N(9.5),
        "setbacks": ParamDef("int", default=3, doc="how many times the tower steps back"),
        "setback_depth": _N(4.0),
        "bays": ParamDef("int", default=9, doc="piers-and-window bays across the front"),
        "crown": ParamDef("bool", default=True, doc="stepped crown and spire"),
        "street": ParamDef("bool", default=True),
    },
    part_tags=("base", "wall", "wall_b", "trim", "sash", "glass", "door", "soot", "iron", "groove", "roof",
               "ground", "curb", "road"),
    tiled_tags=frozenset({"base", "wall", "wall_b", "soot", "roof", "ground", "road"}),
    big_tags=frozenset({"wall", "trim", "iron"}),
    no_collide_tags=frozenset({"trim", "sash", "iron", "glass", "groove"}),
    validate=validate,
    makes=("art deco tower", "art deco skyscraper", "art deco building", "skyscraper", "tower block"),
    not_for=("house", "cabin", "church"),
)
