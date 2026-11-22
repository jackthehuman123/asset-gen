from rbxasset.builders import rules
from rbxasset.builders.vocab import ParamDef, Vocab

_N = lambda d, doc="": ParamDef("number", default=d, doc=doc)  # noqa: E731


def validate(p, budgets):
    rules.num(p, "height", 3.0, 30.0)
    rules.num(p, "base_radius", 0.2, 2.0)
    rules.num(p, "base_height", 0.4, 4.0)
    rules.num(p, "pole_radius", 0.05, 0.6)
    rules.num(p, "arm_length", 0.0, 4.0)
    rules.num(p, "head_radius", 0.15, 1.5)
    rules.choice(p, "head_style", ("lantern", "globe"))
    if p["base_height"] + p["head_radius"] * 2.2 + 0.5 > p["height"]:
        raise ValueError("height %r is too short for base_height %r plus the head"
                         % (p["height"], p["base_height"]))


VOCAB = Vocab(
    params={
        "height": _N(12.0, "ground to the top of the head"),
        "base_radius": _N(0.45),
        "base_height": _N(1.2),
        "pole_radius": _N(0.14),
        "arm_length": _N(1.2, "sideways arm to the head; 0 puts the head on top"),
        "head_style": ParamDef("string", default="lantern", doc="lantern or globe"),
        "head_radius": _N(0.45),
    },
    part_tags=("base", "pole", "arm", "head", "lens"),
    tiled_tags=frozenset(),
    big_tags=frozenset({"pole", "head"}),
    no_collide_tags=frozenset({"head", "lens", "arm"}),
    validate=validate,
    makes=("lamp post", "lamppost", "street lamp", "street light", "bollard", "signpost", "flagpole"),
    not_for=("tree", "tower", "building", "chandelier"),
)
