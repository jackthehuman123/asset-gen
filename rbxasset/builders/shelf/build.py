"""Open shelf unit: sides, top, plinth, shelves, optional back. Runs inside Blender."""
import random
from typing import Dict

from rbxasset.builders.kit import Kit
from rbxasset.builders.kit_shots import default_shots
from rbxasset.builders.result import BuildResult

TAGS = ("frame", "shelves", "back")
PLINTH = 0.25


def build(params: Dict, rng: random.Random) -> BuildResult:
    W, D, H, n, t = params["width"], params["depth"], params["height"], params["shelf_count"], params["board_thickness"]
    k = Kit(TAGS)
    for sx in (-1, 1):
        k.box("frame", (t, D, H), (sx * (W / 2 - t / 2), 0, H / 2))
    k.box("frame", (W, D, t), (0, 0, H - t / 2))
    k.box("frame", (W - 2 * t, D - 0.1, PLINTH), (0, 0.02, PLINTH / 2))
    bp = 0.06 if params["back_panel"] else 0.0
    zb = PLINTH + t / 2
    sp = (H - t - zb) / (n + 1)
    for i in range(n + 1):
        k.box("shelves", (W - 2 * t, D - bp, t), (0, -bp / 2, zb + i * sp))
    if params["back_panel"]:
        k.box("back", (W - 2 * t, bp, H - t - PLINTH), (0, D / 2 - bp / 2, PLINTH + (H - t - PLINTH) / 2))
    return BuildResult(k.parts, default_shots(W, D, H), {"W": W, "H": H})
