from rbxasset.builders.vocab import ParamDef, Vocab

_N = lambda d, doc="": ParamDef("number", default=d, doc=doc)  # noqa: E731

VOCAB = Vocab(
    params={
        "width": _N(28, "house width"),
        "depth": _N(20, "house depth"),
        "plinth_height": _N(1.0),
        "floor_height": _N(1.6),
        "wall_height": _N(10),
        "wainscot_height": _N(4),
        "post_size": _N(0.8),
        "roof_pitch_deg": _N(30),
        "eave_overhang": _N(3.2),
        "gable_overhang": _N(1.5),
        "engawa_depth": _N(3),
        "sill_height": _N(3.2),
        "window_height": _N(3.6),
        "door_height": _N(7.5),
        "facades": ParamDef("object", default={
            "front": ["wall", "window", "door", "door", "window", "wall"],
            "back": ["wall", "window", "wall", "wall", "window", "wall"],
            "left": ["wall", "window", "window", "wall"],
            "right": ["wall", "window", "wall", "wall"],
        }, doc="per-side bay lists of wall/window/door"),
        "boarded": ParamDef("list", default=[["front", 4]], doc="[side, bay] windows boarded up"),
        "door_open": ParamDef("list", default=[["front", 3, 0.6]], doc="[side, bay, amount]"),
        "seed": ParamDef("int", default=13, doc="damage seed"),
        "roof_sag": _N(0.6),
        "missing_tiles": _N(0.07),
        "slipped_tiles": _N(0.06),
        "missing_boards": _N(0.08),
        "broken_boards": _N(0.12),
        "broken_lattice": _N(0.2),
        "missing_engawa_planks": _N(0.12),
    },
    part_tags=("foundation", "frame", "siding", "plaster", "lattice", "doors", "boards",
               "engawa", "roof_base", "tiles_front", "tiles_back", "ridge", "eaves", "gable"),
    tiled_tags=frozenset({"siding", "plaster", "roof_base", "foundation", "gable"}),
    big_tags=frozenset({"frame", "engawa", "tiles_front", "tiles_back"}),
    no_collide_tags=frozenset({"lattice", "tiles_front", "tiles_back", "ridge", "eaves"}),
)
