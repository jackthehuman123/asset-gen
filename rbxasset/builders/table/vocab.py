from rbxasset.builders import rules
from rbxasset.builders.vocab import ParamDef, Vocab

_N = lambda d, doc="": ParamDef("number", default=d, doc=doc)  # noqa: E731


def validate(p, budgets):
    rules.num(p, "width", 1.0, 14.0)
    rules.num(p, "depth", 1.0, 14.0)
    rules.num(p, "height", 1.0, 6.0)
    rules.num(p, "top_thickness", 0.05, 0.6)
    rules.num(p, "leg_size", 0.1, 0.8)
    rules.num(p, "apron_height", 0.0, 1.2)
    rules.choice(p, "leg_shape", ("square", "round"))
    if p["top_thickness"] >= p["height"] / 2:
        raise ValueError("top_thickness must be under half of height, got %r" % p["top_thickness"])


VOCAB = Vocab(
    params={
        "width": _N(5.0, "top width in studs"),
        "depth": _N(2.8, "top depth"),
        "height": _N(2.4, "floor to top surface"),
        "top_thickness": _N(0.16),
        "leg_size": _N(0.22, "leg width (square) or diameter (round)"),
        "leg_shape": ParamDef("string", default="square", doc="square or round"),
        "apron_height": _N(0.4, "rail under the top; 0 for none"),
        "stretchers": ParamDef("bool", default=True, doc="low rails between the legs"),
    },
    part_tags=("top", "legs", "apron", "stretchers"),
    tiled_tags=frozenset(),
    big_tags=frozenset({"top"}),
    no_collide_tags=frozenset(),
    validate=validate,
    makes=("table", "dining table", "coffee table", "desk", "workbench", "counter"),
    not_for=("chair", "bench", "shelf", "sofa", "bed"),
)
