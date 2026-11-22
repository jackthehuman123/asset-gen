from rbxasset.builders.vocab import ParamDef, Vocab

_N = lambda d, doc="": ParamDef("number", default=d, doc=doc)  # noqa: E731


def validate(params, budgets):
    """bpy-free pre-Blender checks. Raises ValueError naming the bad value."""
    for k, lo, hi in (("width", 1.5, 6.0), ("depth", 1.5, 6.0), ("height", 4.0, 14.0)):
        if not lo <= params[k] <= hi:
            raise ValueError("%s must be between %s and %s studs, got %r" % (k, lo, hi, params[k]))
    for k, lo, hi in (("pane_cols", 1, 6), ("pane_rows", 1, 14)):
        v = params[k]
        if isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi:
            raise ValueError("%s must be a whole number from %d to %d, got %r" % (k, lo, hi, v))
    if params["roof_rise"] < 0 or params["roof_rise"] > params["height"] / 4:
        raise ValueError("roof_rise must be between 0 and height/4, got %r" % params["roof_rise"])


VOCAB = Vocab(
    params={
        "width": _N(2.9, "outer width in studs (about 3 studs per metre)"),
        "depth": _N(2.9, "outer depth in studs"),
        "height": _N(7.6, "height from ground to the base of the roof"),
        "plinth_height": _N(0.25, "stepped base height"),
        "post_size": _N(0.18, "corner post thickness"),
        "pane_cols": ParamDef("int", default=3, doc="glazing columns per side"),
        "pane_rows": ParamDef("int", default=8, doc="glazing rows per side"),
        "roof_rise": _N(0.55, "how far the domed roof rises above its base"),
        "sign_height": _N(0.5, "height of the sign panel under the roof"),
        "glazing": ParamDef("bool", default=True, doc="include the glazing mesh (set to Glass in Studio)"),
    },
    part_tags=("base", "frame", "door", "roof", "sign", "glazing", "handle"),
    tiled_tags=frozenset(),
    big_tags=frozenset({"frame", "door"}),
    no_collide_tags=frozenset({"handle"}),
    validate=validate,
    makes=("phone booth", "phonebooth", "phone box", "telephone box", "telephone kiosk",
           "phone kiosk", "kiosk"),
    not_for=("diner booth", "photo booth", "walk-in room", "building", "house", "shed",
             "cabinet"),
)
