from rbxasset.builders import rules
from rbxasset.builders.roofs_forms import FORMS
from rbxasset.builders.vocab import ParamDef, Vocab

_N = lambda d, doc="": ParamDef("number", default=d, doc=doc)  # noqa: E731


def validate(p, budgets):
    rules.num(p, "width", 10.0, 40.0)
    rules.num(p, "depth", 8.0, 30.0)
    rules.whole(p, "storeys", 1, 3)
    rules.num(p, "storey_height", 6.5, 14.0)
    rules.num(p, "foundation_height", 0.3, 4.0)
    rules.choice(p, "roof_form", FORMS)
    rules.num(p, "roof_pitch", 10.0, 60.0)
    rules.num(p, "eave", 0.3, 4.0)
    rules.whole(p, "bays", 2, 6)
    rules.whole(p, "side_windows", 0, 4)
    rules.whole(p, "back_windows", 0, 5)
    rules.num(p, "porch_depth", 2.0, 8.0)
    if p["width"] < p["depth"]:
        raise ValueError("width %r must be at least depth %r (the ridge runs along the width)"
                         % (p["width"], p["depth"]))
    if p["bays"] * 3.2 > p["width"]:
        raise ValueError("%d bays do not fit in width %r" % (p["bays"], p["width"]))
    if p["side_windows"] * 3.2 > p["depth"] or p["back_windows"] * 3.2 > p["width"]:
        raise ValueError("too many windows for the wall length")


VOCAB = Vocab(
    params={
        "width": _N(20.0, "front width in studs (ridge runs along it)"),
        "depth": _N(14.0, "front-to-back depth; not more than width"),
        "storeys": ParamDef("int", default=1, doc="1 to 3"),
        "storey_height": _N(8.5),
        "foundation_height": _N(1.2),
        "roof_form": ParamDef("string", default="gable", doc="gable, hip, gambrel or saltbox"),
        "roof_pitch": _N(30.0, "degrees"),
        "eave": _N(1.5, "roof overhang"),
        "bays": ParamDef("int", default=3, doc="window/door bays across the front; door in the middle one"),
        "side_windows": ParamDef("int", default=2, doc="per floor, each side"),
        "back_windows": ParamDef("int", default=2, doc="per floor"),
        "porch": ParamDef("bool", default=True),
        "porch_depth": _N(4.0),
        "chimney": ParamDef("bool", default=True),
    },
    part_tags=("foundation", "walls", "trim", "roof", "door", "glazing", "chimney"),
    tiled_tags=frozenset({"foundation", "walls", "roof"}),
    big_tags=frozenset({"walls", "roof"}),
    no_collide_tags=frozenset({"trim"}),
    validate=validate,
    makes=("house", "detached house", "cottage", "farmhouse", "bungalow", "colonial house",
           "suburban house", "family house"),
    not_for=("rowhouse", "skyscraper", "castle", "tent", "mansion"),
)
