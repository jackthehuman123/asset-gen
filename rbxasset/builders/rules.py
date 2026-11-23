"""Small bpy-free validation helpers shared by builder vocabs."""


def num(params, key, lo, hi):
    v = params[key]
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not lo <= v <= hi:
        raise ValueError("%s must be a number from %s to %s, got %r" % (key, lo, hi, v))


def whole(params, key, lo, hi):
    v = params[key]
    if isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi:
        raise ValueError(
            "%s must be a whole number from %d to %d, got %r" % (key, lo, hi, v)
        )


def choice(params, key, allowed):
    if params[key] not in allowed:
        raise ValueError(
            "%s must be one of %s, got %r" % (key, ", ".join(allowed), params[key])
        )
