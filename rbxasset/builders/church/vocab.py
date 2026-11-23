from rbxasset.builders import rules
from rbxasset.builders.vocab import ParamDef, Vocab

_N = lambda d, doc="": ParamDef("number", default=d, doc=doc)  # noqa: E731


def validate(p, budgets):
    rules.num(p, "nave_width", 14.0, 36.0)
    rules.num(p, "nave_length", 30.0, 90.0)
    rules.num(p, "wall_height", 16.0, 36.0)
    rules.num(p, "tower_width", 9.0, 18.0)
    rules.num(p, "tower_height", 30.0, 80.0)
    rules.num(p, "spire_height", 12.0, 50.0)
    rules.whole(p, "bays", 3, 8)
    if p["tower_width"] > p["nave_width"]:
        raise ValueError("tower_width %r cannot exceed nave_width %r" % (p["tower_width"], p["nave_width"]))
    if p["tower_height"] < p["wall_height"] + 6:
        raise ValueError("tower_height %r must clear the nave wall height %r" % (p["tower_height"], p["wall_height"]))


VOCAB = Vocab(
    params={
        "nave_width": _N(22.0),
        "nave_length": _N(52.0),
        "wall_height": _N(24.0, "nave wall to the eaves"),
        "tower_width": _N(13.0),
        "tower_height": _N(46.0, "to the base of the spire"),
        "spire_height": _N(26.0),
        "bays": ParamDef("int", default=5, doc="lancet windows and buttresses per side"),
        "street": ParamDef("bool", default=True),
    },
    part_tags=("base", "wall", "wall_b", "trim", "sash", "glass", "door", "soot", "iron", "roof", "ground",
               "curb", "road"),
    tiled_tags=frozenset({"base", "wall", "wall_b", "soot", "roof", "ground", "road"}),
    big_tags=frozenset({"wall", "trim", "roof"}),
    no_collide_tags=frozenset({"trim", "sash", "iron", "glass"}),
    validate=validate,
    makes=("church", "chapel", "cathedral", "parish church"),
    not_for=("house", "skyscraper", "barn"),
)
