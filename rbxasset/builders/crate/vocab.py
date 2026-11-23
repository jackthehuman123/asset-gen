from rbxasset.builders import rules
from rbxasset.builders.vocab import ParamDef, Vocab

_N = lambda d, doc="": ParamDef("number", default=d, doc=doc)  # noqa: E731


def validate(p, budgets):
    rules.num(p, "width", 0.8, 10.0)
    rules.num(p, "depth", 0.8, 10.0)
    rules.num(p, "height", 0.6, 8.0)
    rules.whole(p, "board_count", 2, 10)
    rules.num(p, "board_thickness", 0.04, 0.4)
    rules.num(p, "batten_size", 0.08, 0.6)
    if p["height"] / p["board_count"] < 0.15:
        raise ValueError(
            "board_count %d is too many for height %r" % (p["board_count"], p["height"])
        )


VOCAB = Vocab(
    params={
        "width": _N(2.4),
        "depth": _N(2.0),
        "height": _N(1.8, "box height, not counting the lid"),
        "board_count": ParamDef("int", default=4, doc="boards stacked per side"),
        "board_thickness": _N(0.1),
        "batten_size": _N(0.18, "corner posts"),
        "lid": ParamDef("bool", default=True),
    },
    part_tags=("boards", "battens", "lid"),
    tiled_tags=frozenset(),
    big_tags=frozenset({"boards"}),
    no_collide_tags=frozenset(),
    validate=validate,
    makes=("crate", "wooden crate", "chest", "trunk"),
    not_for=("barrel", "cabinet", "phone box", "safe"),
)
