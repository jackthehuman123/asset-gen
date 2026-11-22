from rbxasset.builders import rules
from rbxasset.builders.vocab import ParamDef, Vocab

_N = lambda d, doc="": ParamDef("number", default=d, doc=doc)  # noqa: E731


def validate(p, budgets):
    rules.num(p, "width", 1.0, 12.0)
    rules.num(p, "depth", 0.4, 4.0)
    rules.num(p, "height", 1.5, 10.0)
    rules.num(p, "board_thickness", 0.05, 0.4)
    rules.whole(p, "shelf_count", 1, 12)
    gap = (p["height"] - p["board_thickness"] - 0.25) / (p["shelf_count"] + 1)
    if gap < 0.5:
        raise ValueError("shelf_count %d leaves under 0.5 studs between shelves at height %s"
                         % (p["shelf_count"], p["height"]))


VOCAB = Vocab(
    params={
        "width": _N(3.6),
        "depth": _N(1.0),
        "height": _N(6.0),
        "shelf_count": ParamDef("int", default=4, doc="inner shelves, plus the bottom one"),
        "board_thickness": _N(0.1),
        "back_panel": ParamDef("bool", default=True),
    },
    part_tags=("frame", "shelves", "back"),
    tiled_tags=frozenset(),
    big_tags=frozenset({"frame", "shelves"}),
    no_collide_tags=frozenset(),
    validate=validate,
    makes=("shelf", "bookshelf", "shelving unit", "rack"),
    not_for=("cabinet", "wardrobe", "locker", "display case"),
)
