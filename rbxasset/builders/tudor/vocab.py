from rbxasset.builders import rules
from rbxasset.builders.vocab import ParamDef, Vocab

_N = lambda d, doc="": ParamDef("number", default=d, doc=doc)  # noqa: E731


def validate(p, budgets):
    rules.num(p, "width", 20.0, 40.0)
    rules.num(p, "depth", 14.0, 28.0)
    rules.num(p, "floor_height", 8.5, 12.0)
    rules.num(p, "roof_pitch", 40.0, 65.0)
    rules.num(p, "jetty", 0.0, 2.5)


VOCAB = Vocab(
    params={
        "width": _N(28.0),
        "depth": _N(18.0),
        "floor_height": _N(9.5),
        "roof_pitch": _N(55.0, "degrees; Tudor roofs are very steep"),
        "jetty": _N(1.3, "upper floor overhang on the front"),
        "street": ParamDef("bool", default=True),
    },
    part_tags=("base", "wall", "wall_b", "timber", "trim", "sash", "glass", "door", "soot", "iron", "brick",
               "roof", "ground", "curb", "road"),
    tiled_tags=frozenset({"base", "wall", "wall_b", "brick", "roof", "ground", "road"}),
    big_tags=frozenset({"wall", "roof", "timber"}),
    no_collide_tags=frozenset({"trim", "sash", "iron", "glass", "timber"}),
    validate=validate,
    makes=("tudor house", "tudor", "half timbered house", "timber framed house"),
    not_for=("skyscraper", "cabin", "barn"),
)
