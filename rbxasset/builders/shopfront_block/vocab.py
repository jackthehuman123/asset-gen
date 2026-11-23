from rbxasset.builders import rules
from rbxasset.builders.vocab import ParamDef, Vocab

_N = lambda d, doc="": ParamDef("number", default=d, doc=doc)  # noqa: E731


def validate(p, budgets):
    rules.num(p, "width", 28.0, 70.0)
    rules.num(p, "depth", 20.0, 40.0)
    rules.whole(p, "floors", 2, 4)
    rules.num(p, "floor_height", 9.0, 12.0)
    rules.whole(p, "shops", 2, 5)
    if p["shops"] * 12.0 > p["width"]:
        raise ValueError("%d shops do not fit in width %r" % (p["shops"], p["width"]))


VOCAB = Vocab(
    params={
        "width": _N(44.0),
        "depth": _N(28.0),
        "floors": ParamDef("int", default=3, doc="storeys including the shop floor"),
        "floor_height": _N(10.5),
        "shops": ParamDef("int", default=3, doc="storefronts across the ground floor"),
        "awnings": ParamDef("bool", default=True),
        "fire_escape": ParamDef("bool", default=True),
        "street": ParamDef("bool", default=True),
    },
    part_tags=(
        "wall",
        "wall_b",
        "trim",
        "sash",
        "glass",
        "door",
        "sign",
        "awning",
        "awning_b",
        "soot",
        "iron",
        "groove",
        "roof",
        "ground",
        "curb",
        "road",
    ),
    tiled_tags=frozenset({"wall", "wall_b", "soot", "roof", "ground", "road"}),
    big_tags=frozenset({"wall", "trim", "iron"}),
    no_collide_tags=frozenset(
        {"trim", "sash", "iron", "glass", "groove", "awning", "awning_b", "sign"}
    ),
    validate=validate,
    makes=(
        "shop building",
        "storefront",
        "main street building",
        "mixed use building",
        "corner store",
        "shopfront",
    ),
    not_for=("house", "skyscraper", "church"),
)
