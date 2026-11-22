"""STYLE.md parsing and game/area layering. bpy-free, Python 3.9 compatible.

A STYLE.md is free prose plus exactly one fenced block opened with
```json style. Keys in that block: "intent" (becomes Style.intent_game for the
game file and Style.intent_area for the area file), "camera", "studs_per_tile",
"budgets", "lighting" (game-only, see LOCKED_KEYS), "palette", "finishes",
"wear", "avoid".
"""
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

LOCKED_KEYS = ("camera", "studs_per_tile", "budgets", "lighting")
MAX_TRIS = 20000
MAX_TEXTURE = 1024

_FENCE = re.compile(r"^```json style[ \t]*\n(.*?)^```[ \t]*$", re.S | re.M)


class StyleError(Exception):
    pass


def parse_style_md(text: str) -> dict:
    blocks = _FENCE.findall(text)
    if len(blocks) != 1:
        raise StyleError(
            "STYLE.md needs exactly one ```json style block, found %d" % len(blocks))
    try:
        data = json.loads(blocks[0])
    except ValueError as e:
        raise StyleError("invalid JSON in ```json style block: %s" % e)
    if not isinstance(data, dict):
        raise StyleError("```json style block must be a JSON object")
    return data


@dataclass
class Style:
    intent_game: str
    intent_area: str
    camera: str
    studs_per_tile: float
    budgets: Dict
    lighting: Dict
    palette: Dict
    finishes: Dict[str, Dict]
    wear: Dict
    avoid: List[str] = field(default_factory=list)


def _read(path: Path) -> dict:
    return parse_style_md(Path(path).read_text(encoding="utf-8"))


def load_style(game_md: Path, area_md: Path) -> Style:
    game = _read(game_md)
    area = _read(area_md)
    for key in LOCKED_KEYS:
        if key in area:
            raise StyleError(
                "area STYLE.md may not set '%s'; it is game-level only (locked keys: %s)"
                % (key, ", ".join(LOCKED_KEYS)))
    camera = game.get("camera", "first_person")
    if camera not in ("first_person", "third_person"):
        raise StyleError("camera must be 'first_person' or 'third_person', got %r" % camera)
    studs = float(game.get("studs_per_tile", 4 if camera == "first_person" else 8))
    budgets = {"max_tris_per_mesh": MAX_TRIS, "texture_big": 1024, "texture_small": 512}
    budgets.update(game.get("budgets", {}))
    if budgets["max_tris_per_mesh"] > MAX_TRIS:
        raise StyleError("budgets.max_tris_per_mesh %s exceeds Roblox limit %d"
                         % (budgets["max_tris_per_mesh"], MAX_TRIS))
    for k in ("texture_big", "texture_small"):
        if budgets[k] > MAX_TEXTURE:
            raise StyleError("budgets.%s %s exceeds Roblox limit %d"
                             % (k, budgets[k], MAX_TEXTURE))
    finishes = dict(game.get("finishes", {}))
    finishes.update(area.get("finishes", {}))
    palette = dict(game.get("palette", {}))
    palette.update(area.get("palette", {}))
    wear = dict(game.get("wear", {}))
    wear.update(area.get("wear", {}))
    return Style(
        intent_game=game.get("intent", ""),
        intent_area=area.get("intent", ""),
        camera=camera,
        studs_per_tile=studs,
        budgets=budgets,
        lighting=game.get("lighting", {"preset": "overcast_exterior"}),
        palette=palette,
        finishes=finishes,
        wear=wear,
        avoid=list(game.get("avoid", [])) + list(area.get("avoid", [])),
    )
