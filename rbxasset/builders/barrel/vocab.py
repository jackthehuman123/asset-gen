from rbxasset.builders import rules
from rbxasset.builders.vocab import ParamDef, Vocab

_N = lambda d, doc="": ParamDef("number", default=d, doc=doc)  # noqa: E731


def validate(p, budgets):
    rules.num(p, "height", 0.8, 8.0)
    rules.num(p, "radius", 0.3, 4.0)
    rules.num(p, "bulge", 0.0, 0.5)
    rules.whole(p, "hoop_count", 2, 6)
    rules.num(p, "wall", 0.03, 0.4)
    if p["wall"] >= p["radius"] / 2:
        raise ValueError("wall must be under half of radius, got %r" % p["wall"])


VOCAB = Vocab(
    params={
        "height": _N(2.6),
        "radius": _N(1.0, "radius at the ends"),
        "bulge": _N(0.18, "extra radius at the belly, as a fraction"),
        "hoop_count": ParamDef("int", default=3),
        "wall": _N(0.1, "wall thickness when open"),
        "open_top": ParamDef("bool", default=False, doc="hollow with no lid"),
    },
    part_tags=("body", "hoops", "lid"),
    tiled_tags=frozenset(),
    big_tags=frozenset({"body"}),
    no_collide_tags=frozenset(),
    validate=validate,
    makes=("barrel", "keg", "cask", "drum", "bin", "trash can"),
    not_for=("crate", "tank", "pipe", "chimney"),
)
