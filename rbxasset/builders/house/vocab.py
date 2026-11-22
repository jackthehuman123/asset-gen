from rbxasset.builders.house import roof_math
from rbxasset.builders.vocab import ParamDef, Vocab

SIDES = ("front", "back", "left", "right")
BAY_KINDS = ("wall", "window", "door")


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def validate(params, budgets):
    """bpy-free pre-Blender checks. Raises ValueError with the bad value and the allowed ones."""
    fac = params["facades"]
    bad = sorted(set(fac) - set(SIDES))
    if bad:
        raise ValueError("facades has unknown side(s) %s; allowed: %s" % (bad, ", ".join(SIDES)))
    for side in SIDES:
        if side not in fac:
            raise ValueError("facades is missing side '%s'; all four are required: %s"
                             % (side, ", ".join(SIDES)))
        bays = fac[side]
        if not isinstance(bays, list) or not bays:
            raise ValueError("facades.%s must be a non-empty list of bays, got %r" % (side, bays))
        for i, kind in enumerate(bays):
            if kind not in BAY_KINDS:
                raise ValueError("facades.%s[%d] is %r; allowed bay kinds: %s"
                                 % (side, i, kind, ", ".join(BAY_KINDS)))

    def target(name, entry, n, want_kind):
        if not isinstance(entry, list) or len(entry) != n:
            raise ValueError("%s entry %r must be a list of %d items" % (name, entry, n))
        side, idx = entry[0], entry[1]
        if side not in SIDES:
            raise ValueError("%s entry %r: side %r; allowed: %s" % (name, entry, side, ", ".join(SIDES)))
        if isinstance(idx, bool) or not isinstance(idx, int) or not 0 <= idx < len(fac[side]):
            raise ValueError("%s entry %r: bay index %r out of range 0..%d for side '%s'"
                             % (name, entry, idx, len(fac[side]) - 1, side))
        if fac[side][idx] != want_kind:
            raise ValueError("%s entry %r targets a %s; it must target a %s"
                             % (name, entry, fac[side][idx], want_kind))

    for e in params["boarded"]:
        target("boarded", e, 2, "window")
    for e in params["door_open"]:
        target("door_open", e, 3, "door")
        if not _num(e[2]) or not 0 <= e[2] <= 1:
            raise ValueError("door_open entry %r: amount must be a number 0..1" % (e,))

    limit = budgets["max_tris_per_mesh"]
    args = (params["depth"], params["roof_pitch_deg"], params["eave_overhang"],
            params["gable_overhang"])
    est = roof_math.estimate_tile_tris(params["width"], *args)
    if est > limit:
        raise ValueError(
            "tiles_front = about %d tris > max_tris_per_mesh %d; max width at depth %s, pitch %s "
            "is about %s" % (est, limit, params["depth"], params["roof_pitch_deg"],
                             roof_math.max_width(limit, *args)))

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
    validate=validate,
    makes=("japanese house", "japanese farmhouse", "minka", "machiya", "village house"),
    not_for=("multi-storey building", "shrine", "temple", "tower", "skyscraper",
             "interior room", "domed structure", "round building"),
)
