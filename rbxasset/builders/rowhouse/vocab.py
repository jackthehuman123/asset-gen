from rbxasset.builders import rules
from rbxasset.builders.vocab import ParamDef, Vocab

_N = lambda d, doc="": ParamDef("number", default=d, doc=doc)  # noqa: E731


def validate(p, budgets):
    rules.num(p, "width", 9.0, 24.0)
    rules.num(p, "depth", 16.0, 60.0)
    rules.whole(p, "floors", 2, 5)
    rules.num(p, "floor_height", 7.5, 13.0)
    rules.num(p, "basement_height", 2.0, 6.0)
    rules.whole(p, "bays", 2, 4)
    if p["bays"] * 3.3 > p["width"]:
        raise ValueError("%d bays do not fit in width %r" % (p["bays"], p["width"]))


VOCAB = Vocab(
    params={
        "width": _N(
            14.0,
            "party-wall to party-wall; a real rowhouse is 14-18 ft, about 13-16 studs",
        ),
        "depth": _N(36.0),
        "floors": ParamDef(
            "int", default=4, doc="storeys above the raised basement (2-5)"
        ),
        "floor_height": _N(9.5),
        "basement_height": _N(3.6, "raised basement under the stoop"),
        "bays": ParamDef(
            "int",
            default=2,
            doc="windows across the front; the door takes the first bay",
        ),
        "stoop": ParamDef("bool", default=True),
        "cornice": ParamDef("bool", default=True),
    },
    part_tags=("foundation", "walls", "trim", "roof", "door", "glazing"),
    tiled_tags=frozenset({"foundation", "walls"}),
    big_tags=frozenset({"walls"}),
    no_collide_tags=frozenset({"trim"}),
    validate=validate,
    makes=("rowhouse", "row house", "townhouse", "terraced house", "terrace house"),
    not_for=("detached house", "skyscraper", "apartment block", "castle"),
)
