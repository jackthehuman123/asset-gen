from rbxasset.builders import rules
from rbxasset.builders.vocab import ParamDef, Vocab

_N = lambda d, doc="": ParamDef("number", default=d, doc=doc)  # noqa: E731


def validate(p, budgets):
    rules.num(p, "width", 16.0, 80.0)
    rules.num(p, "depth", 12.0, 60.0)
    rules.whole(p, "floors", 2, 14)
    rules.num(p, "floor_height", 6.5, 12.0)
    rules.whole(p, "columns", 2, 14)
    rules.whole(p, "side_columns", 0, 10)
    if p["columns"] * 3.4 > p["width"] or p["side_columns"] * 3.4 > p["depth"]:
        raise ValueError("too many window columns for the wall length")
    windows = p["floors"] * (2 * p["columns"] + 2 * p["side_columns"])
    if windows > 130:
        raise ValueError(
            "%d windows exceed the triangle budget (max 130); reduce floors or columns"
            % windows
        )


VOCAB = Vocab(
    params={
        "width": _N(36.0),
        "depth": _N(22.0),
        "floors": ParamDef("int", default=6),
        "floor_height": _N(8.0),
        "columns": ParamDef("int", default=6, doc="window columns on front and back"),
        "side_columns": ParamDef("int", default=3, doc="window columns on each side"),
    },
    part_tags=("foundation", "walls", "trim", "roof", "door", "glazing"),
    tiled_tags=frozenset({"foundation", "walls"}),
    big_tags=frozenset({"walls"}),
    no_collide_tags=frozenset({"trim"}),
    validate=validate,
    makes=(
        "apartment building",
        "apartment block",
        "apartment",
        "flats",
        "condo building",
        "office building",
    ),
    not_for=("skyscraper", "house", "rowhouse", "castle"),
)
