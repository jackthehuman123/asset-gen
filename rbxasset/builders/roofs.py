"""Roof forms for buildings whose ridge runs along x. Runs inside Blender.

roof(kit, tags, form, W, D, zE, pitch_deg, eave) builds slabs (tag tags['roof']) and gable-end fill
(tags['wall']) and returns (apex_z, created_objects). Forms: gable, hip, gambrel, saltbox.
Requires W >= D (the ridge follows the long side)."""
import math

FORMS = ("gable", "hip", "gambrel", "saltbox")
SLAB_T, END_T = 0.22, 0.3


def _slab(kit, tag, p0, p1, x_len):
    dy, dz = p1[0] - p0[0], p1[1] - p0[1]
    length = math.hypot(dy, dz)
    a = math.atan2(dz, dy)
    my = (p0[0] + p1[0]) / 2 - math.sin(a) * SLAB_T / 2
    mz = (p0[1] + p1[1]) / 2 + math.cos(a) * SLAB_T / 2
    return kit.box(tag_name(kit), (x_len, length, SLAB_T), (0, my, mz), rot=(a, 0, 0), bevel=0.0)


_TAG = {}


def tag_name(kit):
    return _TAG[id(kit)]


def roof(kit, tags, form, W, D, zE, pitch_deg, eave):
    if form not in FORMS:
        raise ValueError("roof form must be one of %s, got %r" % (", ".join(FORMS), form))
    tp = math.tan(math.radians(pitch_deg))
    objs = []
    if form == "hip":
        X, Y = W / 2 + eave, D / 2 + eave
        zb = zE - eave * tp
        half = D / 2
        zt = zE + half * tp
        rl = max(0.0, W / 2 - D / 2)
        b = [(-X, -Y, zb), (X, -Y, zb), (X, Y, zb), (-X, Y, zb)]
        if rl > 0.05:
            v = b + [(-rl, 0, zt), (rl, 0, zt)]
            faces = [[3, 2, 1, 0], [0, 1, 5, 4], [1, 2, 5], [2, 3, 4, 5], [3, 0, 4]]
        else:
            v = b + [(0, 0, zt)]
            faces = [[3, 2, 1, 0], [0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]]
        objs.append(kit.mesh(tags["roof"], v, faces))
        return zt, objs
    if form == "gable":
        R = D / 2 * tp
        line = [(-D / 2 - eave, zE - eave * tp), (0, zE + R), (D / 2 + eave, zE - eave * tp)]
        fill = [(-D / 2, zE), (D / 2, zE), (0, zE + R)]
        apex = zE + R
    elif form == "gambrel":
        e = min(eave, 0.6)
        t60, t25 = math.tan(math.radians(60)), math.tan(math.radians(25))
        kz = zE + D / 4 * t60
        apex = kz + D / 4 * t25
        line = [(-D / 2 - e, zE - e * t60), (-D / 4, kz), (0, apex), (D / 4, kz), (D / 2 + e, zE - e * t60)]
        fill = [(-D / 2, zE), (D / 2, zE), (D / 4, kz), (0, apex), (-D / 4, kz)]
    else:  # saltbox: ridge nearer the front, long gentle back slope
        yr = -D / 2 + D * 0.38
        front_tp = math.tan(math.radians(pitch_deg * 1.2))
        apex = zE + (yr + D / 2) * front_tp
        back_tp = (apex - zE) / (D / 2 - yr)
        line = [(-D / 2 - eave, zE - eave * front_tp), (yr, apex), (D / 2 + eave, zE - eave * back_tp)]
        fill = [(-D / 2, zE), (D / 2, zE), (yr, apex)]
    _TAG[id(kit)] = tags["roof"]
    for p0, p1 in zip(line, line[1:]):
        objs.append(_slab(kit, tags["roof"], p0, p1, W + 2 * eave))
    for x0, x1 in ((W / 2 - END_T, W / 2), (-W / 2, -W / 2 + END_T)):
        objs.append(kit.prism(tags["wall"], fill, x0, x1))
    return apex, objs
