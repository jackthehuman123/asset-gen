from rbxasset.builders.vocab import ParamDef, Vocab

VOCAB = Vocab(
    params={
        "width": ParamDef("number", default=4.2, doc="overall width in studs"),
        "depth": ParamDef("number", default=1.6, doc="front-to-back depth"),
        "leg_height": ParamDef("number", default=0.55, doc="leg height"),
        "body_height": ParamDef("number", default=2.45, doc="carcass height"),
        "drawer_column_width": ParamDef("number", default=1.4, doc="width of the drawer column"),
    },
    part_tags=("top", "carcass", "fronts", "handles", "legs", "foot_caps"),
    tiled_tags=frozenset(),
    big_tags=frozenset({"carcass", "fronts"}),
    no_collide_tags=frozenset({"handles", "foot_caps"}),
)
