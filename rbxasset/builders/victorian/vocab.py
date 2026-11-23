from rbxasset.builders import rules
from rbxasset.builders.vocab import ParamDef, Vocab

_N = lambda d, doc="": ParamDef("number", default=d, doc=doc)  # noqa: E731


def validate(p, budgets):
    rules.num(p, "width", 22.0, 40.0)
    rules.num(p, "depth", 18.0, 32.0)
    rules.num(p, "floor_height", 8.5, 12.0)
    rules.num(p, "roof_pitch", 35.0, 60.0)


VOCAB = Vocab(
    params={
        "width": _N(28.0),
        "depth": _N(22.0),
        "floor_height": _N(9.5),
        "roof_pitch": _N(48.0, "degrees; Queen Anne roofs are steep"),
        "turret": ParamDef("bool", default=True),
        "porch": ParamDef("bool", default=True),
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
        "victorian house",
        "victorian",
        "queen anne house",
        "painted lady",
        "gingerbread house",
    ),
    not_for=("castle", "skyscraper", "cabin"),
)
