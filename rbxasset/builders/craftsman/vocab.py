from rbxasset.builders import rules
from rbxasset.builders.vocab import ParamDef, Vocab

_N = lambda d, doc="": ParamDef("number", default=d, doc=doc)  # noqa: E731


def validate(p, budgets):
    rules.num(p, "width", 22.0, 40.0)
    rules.num(p, "depth", 24.0, 44.0)
    rules.num(p, "wall_height", 8.0, 12.0)
    rules.num(p, "roof_pitch", 15.0, 32.0)
    rules.num(p, "porch_depth", 5.0, 12.0)
    rules.num(p, "eave", 1.5, 4.5)


VOCAB = Vocab(
    params={
        "width": _N(30.0),
        "depth": _N(30.0),
        "wall_height": _N(9.0),
        "roof_pitch": _N(22.0, "degrees; low and wide"),
        "porch_depth": _N(8.0),
        "eave": _N(3.0, "deep overhang with exposed rafter tails"),
        "street": ParamDef("bool", default=True),
    },
    part_tags=(
        "base",
        "wall",
        "wall_b",
        "shingle",
        "trim",
        "sash",
        "glass",
        "door",
        "soot",
        "iron",
        "brick",
        "roof",
        "ground",
        "curb",
        "road",
    ),
    tiled_tags=frozenset(
        {"base", "wall", "wall_b", "shingle", "brick", "roof", "ground", "road"}
    ),
    big_tags=frozenset({"wall", "roof", "trim"}),
    no_collide_tags=frozenset({"trim", "sash", "iron", "glass"}),
    validate=validate,
    makes=(
        "craftsman house",
        "craftsman",
        "craftsman bungalow",
        "arts and crafts house",
    ),
    not_for=("skyscraper", "castle", "barn"),
)
