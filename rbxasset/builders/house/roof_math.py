"""Roof tile constants and the pre-Blender triangle estimate. bpy-free.

Shared by build.py (which lays the tiles) and vocab.py's validate hook.
"""
import math

TILE_PITCH = 0.6          # one pan + one cover
PAN_HW, PAN_SAG = 0.27, 0.08      # pan half-width, depth of its dish
COVER_HW, COVER_H = 0.13, 0.15    # cover half-width, height of its crown
PAN_SEGS, COVER_SEGS = 3, 4       # profile segments across a tile (shallow pan needs few)
COURSE = 1.1              # target course spacing along the slope
TILE_LEN = 1.35           # tile length (overlaps the course below by TILE_LEN - COURSE)
STEP = 0.12               # a tile's lower end sits this much higher than its upper end
LIP = 0.15                # lip face depth at a tile's lower end
EAVE_LIP = 0.35           # eave tiles: deeper cap hiding the slab edge
TILE_BASE = 0.02          # pan bottom above the slab top
SLAB_T = 0.4
TILE_START = 0.3          # first course's distance down the slope from the ridge
TRIS_PER_CELL = 25        # one pan (12 tris) + one cover (13 tris)


def slab_length(depth, pitch_deg, eave_overhang):
    run = depth / 2 + eave_overhang
    return run / math.cos(math.radians(pitch_deg))


def course_count(slab_l):
    s_end = slab_l + 0.1
    return max(1, int(math.ceil((s_end - TILE_START - TILE_LEN) / COURSE)) + 1)


def column_count(lx):
    return int(lx / TILE_PITCH)


def estimate_tile_tris(width, depth, pitch_deg, eave_overhang, gable_overhang):
    """Worst-case tris for one roof side (missing_tiles = 0)."""
    lx = width + 2 * gable_overhang
    slab_l = slab_length(depth, pitch_deg, eave_overhang)
    return column_count(lx) * course_count(slab_l) * TRIS_PER_CELL


def max_width(max_tris, depth, pitch_deg, eave_overhang, gable_overhang):
    """Largest width whose estimate stays within max_tris."""
    per_col = course_count(slab_length(depth, pitch_deg, eave_overhang)) * TRIS_PER_CELL
    cols = int(max_tris // per_col)
    return math.floor((cols * TILE_PITCH - 2 * gable_overhang) * 10) / 10 - 0.1
