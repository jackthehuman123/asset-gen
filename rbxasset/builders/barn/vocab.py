from rbxasset.builders import rules
from rbxasset.builders.vocab import ParamDef, Vocab

_N = lambda d, doc="": ParamDef("number", default=d, doc=doc)  # noqa: E731


def validate(p, budgets):
    rules.num(p, "width", 14.0, 40.0)
    rules.num(p, "length", 16.0, 70.0)
    rules.num(p, "wall_height", 8.0, 20.0)
    rules.num(p, "door_width", 4.0, 14.0)
    rules.num(p, "door_height", 5.0, 14.0)
    rules.num(p, "eave", 0.3, 3.0)
    if p["door_width"] > p["width"] - 4.0:
        raise ValueError(
            "door_width %r is too wide for width %r" % (p["door_width"], p["width"])
        )
    need = p["door_height"] + (5.0 if p["loft_door"] else 1.0)
    if need > p["wall_height"]:
        raise ValueError(
            "wall_height %r is too low for door_height %r%s"
            % (
                p["wall_height"],
                p["door_height"],
                " plus the loft door" if p["loft_door"] else "",
            )
        )


VOCAB = Vocab(
    params={
        "width": _N(24.0, "gable-end width (x)"),
        "length": _N(34.0, "side length along the ridge (y)"),
        "wall_height": _N(13.0, "ground to the eave"),
        "door_width": _N(9.0),
        "door_height": _N(8.0),
        "loft_door": ParamDef(
            "bool", default=True, doc="small hayloft door above the big doors"
        ),
        "eave": _N(1.2),
    },
    part_tags=("foundation", "walls", "trim", "roof", "door"),
    tiled_tags=frozenset({"foundation", "walls", "roof"}),
    big_tags=frozenset({"walls", "roof"}),
    no_collide_tags=frozenset({"trim"}),
    validate=validate,
    makes=("barn", "stable", "farm shed", "hayloft"),
    not_for=("house", "silo", "greenhouse", "garage"),
)
