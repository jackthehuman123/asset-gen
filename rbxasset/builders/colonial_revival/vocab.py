from rbxasset.builders import rules
from rbxasset.builders.vocab import ParamDef, Vocab

_N = lambda d, doc="": ParamDef("number", default=d, doc=doc)  # noqa: E731


def validate(p, budgets):
    rules.num(p, "width", 26.0, 50.0)
    rules.num(p, "depth", 16.0, 30.0)
    rules.num(p, "floor_height", 9.0, 13.0)
    rules.num(p, "roof_pitch", 25.0, 45.0)
    rules.whole(p, "bays", 3, 7)
    if p["bays"] % 2 == 0:
        raise ValueError("bays must be odd (a central door), got %r" % p["bays"])
    if p["bays"] * 5.0 > p["width"]:
        raise ValueError("%d bays do not fit in width %r" % (p["bays"], p["width"]))


VOCAB = Vocab(
    params={
        "width": _N(38.0),
        "depth": _N(22.0),
        "floor_height": _N(10.5),
        "roof_pitch": _N(32.0),
        "bays": ParamDef("int", default=5, doc="odd; the door is the middle bay"),
        "portico": ParamDef("bool", default=True),
        "street": ParamDef("bool", default=True),
    },
    part_tags=(
        "base",
        "wall",
        "wall_b",
        "trim",
        "sash",
        "glass",
        "door",
        "shutter",
        "soot",
        "iron",
        "brick",
        "roof",
        "ground",
        "curb",
        "road",
    ),
    tiled_tags=frozenset({"base", "wall", "wall_b", "brick", "roof", "ground", "road"}),
    big_tags=frozenset({"wall", "roof", "trim"}),
    no_collide_tags=frozenset({"trim", "sash", "iron", "glass", "shutter"}),
    validate=validate,
    makes=(
        "colonial revival house",
        "georgian house",
        "georgian",
        "federal house",
        "colonial mansion",
    ),
    not_for=("skyscraper", "cabin", "barn"),
)
