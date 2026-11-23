from rbxasset.builders import rules
from rbxasset.builders.vocab import ParamDef, Vocab

_N = lambda d, doc="": ParamDef("number", default=d, doc=doc)  # noqa: E731


def validate(p, budgets):
    rules.whole(p, "steps", 1, 40)
    rules.num(p, "rise", 0.2, 1.2)
    rules.num(p, "run", 0.4, 2.0)
    rules.num(p, "width", 1.0, 12.0)
    rules.num(p, "tread_thickness", 0.05, 0.4)
    if p["tread_thickness"] > p["rise"]:
        raise ValueError(
            "tread_thickness %r cannot exceed rise %r"
            % (p["tread_thickness"], p["rise"])
        )


VOCAB = Vocab(
    params={
        "steps": ParamDef("int", default=6),
        "rise": _N(0.55, "height of one step"),
        "run": _N(0.9, "depth of one step"),
        "width": _N(3.0),
        "tread_thickness": _N(0.12),
        "risers": ParamDef("bool", default=True),
        "stringers": ParamDef(
            "bool", default=True, doc="solid side walls under the flight"
        ),
        "handrail": ParamDef(
            "bool", default=False, doc="posts and sloped rails on both sides"
        ),
    },
    part_tags=("treads", "risers", "stringers", "rail"),
    tiled_tags=frozenset(),
    big_tags=frozenset({"treads"}),
    no_collide_tags=frozenset({"rail"}),
    validate=validate,
    makes=("stairs", "staircase", "stairway", "steps"),
    not_for=("ladder", "ramp", "spiral stair", "escalator"),
)
