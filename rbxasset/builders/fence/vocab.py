from rbxasset.builders import rules
from rbxasset.builders.vocab import ParamDef, Vocab

_N = lambda d, doc="": ParamDef("number", default=d, doc=doc)  # noqa: E731


def validate(p, budgets):
    rules.num(p, "length", 2.0, 60.0)
    rules.num(p, "height", 1.0, 8.0)
    rules.num(p, "post_spacing", 1.0, 20.0)
    rules.num(p, "post_size", 0.1, 1.0)
    rules.whole(p, "rail_count", 1, 4)
    rules.num(p, "picket_width", 0.1, 1.0)
    rules.num(p, "picket_gap", 0.02, 1.0)
    rules.choice(p, "picket_style", ("flat", "pointed"))
    if p["post_spacing"] > p["length"]:
        raise ValueError(
            "post_spacing %r cannot exceed length %r" % (p["post_spacing"], p["length"])
        )
    n = int((p["length"] - p["post_size"]) // (p["picket_width"] + p["picket_gap"]))
    if n * 28 > 19000:
        raise ValueError(
            "too many pickets (%d); lengthen picket_width or picket_gap" % n
        )


VOCAB = Vocab(
    params={
        "length": _N(12.0, "run length along x"),
        "height": _N(3.4),
        "post_spacing": _N(4.0, "target distance between posts"),
        "post_size": _N(0.3),
        "rail_count": ParamDef("int", default=2),
        "picket_width": _N(0.32),
        "picket_gap": _N(0.14),
        "picket_style": ParamDef("string", default="flat", doc="flat or pointed"),
    },
    part_tags=("posts", "rails", "pickets"),
    tiled_tags=frozenset(),
    big_tags=frozenset({"pickets"}),
    no_collide_tags=frozenset(),
    validate=validate,
    makes=("fence", "picket fence", "railing", "balustrade"),
    not_for=("wall", "building", "gate", "hedge"),
)
