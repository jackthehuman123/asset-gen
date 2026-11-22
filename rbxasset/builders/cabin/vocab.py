from rbxasset.builders import rules
from rbxasset.builders.vocab import ParamDef, Vocab

_N = lambda d, doc="": ParamDef("number", default=d, doc=doc)  # noqa: E731


def validate(p, budgets):
    rules.num(p, "width", 10.0, 30.0)
    rules.num(p, "depth", 8.0, 24.0)
    rules.whole(p, "log_courses", 8, 14)
    rules.num(p, "log_radius", 0.3, 0.8)
    rules.num(p, "roof_pitch", 20.0, 55.0)
    rules.num(p, "eave", 0.5, 4.0)
    rules.num(p, "porch_depth", 2.0, 8.0)
    if p["width"] < p["depth"]:
        raise ValueError("width %r must be at least depth %r" % (p["width"], p["depth"]))
    if p["log_courses"] * 2 * p["log_radius"] * 0.88 < 7.0:
        raise ValueError("walls under 7 studs tall leave no room for the door; add courses or thicken logs")


VOCAB = Vocab(
    params={
        "width": _N(16.0, "front width; the ridge runs along it"),
        "depth": _N(12.0),
        "log_courses": ParamDef("int", default=9, doc="stacked logs per wall"),
        "log_radius": _N(0.45),
        "roof_pitch": _N(35.0, "degrees"),
        "eave": _N(1.8),
        "porch": ParamDef("bool", default=True),
        "porch_depth": _N(4.0),
        "chimney": ParamDef("bool", default=True),
    },
    part_tags=("foundation", "logs", "trim", "roof", "door", "glazing", "chimney"),
    tiled_tags=frozenset(),
    big_tags=frozenset({"logs", "roof"}),
    no_collide_tags=frozenset({"trim"}),
    validate=validate,
    makes=("cabin", "log cabin", "hut", "lodge", "chalet"),
    not_for=("tent", "castle", "apartment", "treehouse"),
)
