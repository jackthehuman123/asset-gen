from rbxasset.builders import rules
from rbxasset.builders.vocab import ParamDef, Vocab

_N = lambda d, doc="": ParamDef("number", default=d, doc=doc)  # noqa: E731


def validate(p, budgets):
    rules.num(p, "seat_width", 0.8, 10.0)
    rules.num(p, "seat_depth", 0.8, 4.0)
    rules.num(p, "seat_height", 0.6, 4.0)
    rules.num(p, "back_height", 0.8, 4.0)
    rules.num(p, "leg_size", 0.08, 0.5)
    rules.whole(p, "slat_count", 1, 10)
    rules.choice(p, "back_style", ("slats", "solid", "none"))


VOCAB = Vocab(
    params={
        "seat_width": _N(1.9, "seat width; 5-8 makes a bench"),
        "seat_depth": _N(1.8),
        "seat_height": _N(1.5, "floor to seat top"),
        "back_height": _N(1.9, "backrest height above the seat"),
        "back_style": ParamDef(
            "string", default="slats", doc="slats, solid or none (a stool)"
        ),
        "slat_count": ParamDef("int", default=4),
        "leg_size": _N(0.14),
        "arms": ParamDef("bool", default=False, doc="armrests"),
    },
    part_tags=("seat", "legs", "back", "arms"),
    tiled_tags=frozenset(),
    big_tags=frozenset({"seat", "back"}),
    no_collide_tags=frozenset(),
    validate=validate,
    makes=("chair", "stool", "bench", "armchair", "seat"),
    not_for=("sofa", "bed", "throne", "table"),
)
