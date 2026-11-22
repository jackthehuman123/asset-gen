"""Story decals: transparent RGBA PNGs from mathutils noise. Runs inside Blender.

Muted, dried tones only; abstract stains, no anatomical shapes. Transparent edges.
"""
import math

import bpy
from mathutils import Vector, noise


def _hex(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


def _srgb_to_lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _smooth(x, a, b):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def _n(u, v, scale, off, z=0.0):
    return noise.noise(Vector((u * scale + off, v * scale + off * 0.7, z + off * 0.3))) * 0.5 + 0.5


def _mask(kind, u, v, off):
    if kind == "smear":
        wu = u + (_n(u, v, 3.0, off) - 0.5) * 0.35
        wv = v + (_n(u, v, 3.0, off, 5.0) - 0.5) * 0.35
        blob = 1.0 - math.hypot((wu - 0.5) * 1.1, (wv - 0.68) * 1.5) / 0.38
        body = _smooth(blob, 0.0, 0.25)
        col = _n(u, 0.5, 14.0, off, 9.0)
        length = 0.15 + 0.45 * _n(u, 0.5, 7.0, off, 3.0)
        drip = _smooth(col, 0.55, 0.62) * (1.0 if v < 0.7 else 0.0) * _smooth(v, 0.7 - length, 0.7 - length + 0.12)
        return max(body, drip)
    if kind == "drips":
        col = _n(u, 0.5, 12.0, off, 9.0)
        length = 0.25 + 0.6 * _n(u, 0.5, 5.0, off, 3.0)
        streak = _smooth(col, 0.52, 0.6)
        return streak * _smooth(v, 0.95 - length, 0.95 - length + 0.1) * (1.0 if v < 0.95 else 0.0)
    # splatter: scattered blobs of varying size
    cell = _n(u, v, 9.0, off, 2.0)
    fine = _n(u, v, 28.0, off, 7.0)
    return _smooth(cell * 0.7 + fine * 0.3, 0.62, 0.68)


def render_decal(kind: str, color: str, seed: int, res: int, path: str) -> str:
    off = seed * 17.31 + 3.7
    base = _hex(color)
    pixels = []
    for y in range(res):
        v = (y + 0.5) / res
        for x in range(res):
            u = (x + 0.5) / res
            edge = min(u, 1 - u, v, 1 - v)
            a = _mask(kind, u, v, off) * _smooth(edge, 0.0, 0.1)
            # thick areas read darker and drier; thin edges lighter
            shade = 0.75 + 0.25 * (1.0 - a) + (_n(u, v, 20.0, off, 11.0) - 0.5) * 0.12
            r, g, b = (_srgb_to_lin(min(1.0, max(0.0, c * shade))) for c in base)
            pixels.extend((r, g, b, min(1.0, max(0.0, a))))
    img = bpy.data.images.new("decal_" + kind, res, res, alpha=True)
    img.alpha_mode = "STRAIGHT"
    img.pixels.foreach_set(pixels)
    img.filepath_raw = path
    img.file_format = "PNG"
    scene = bpy.context.scene
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    img.save()
    return path
