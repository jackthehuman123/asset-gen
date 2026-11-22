"""Vocabulary types describing what a builder accepts. bpy-free."""
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, Tuple

PARAM_TYPES = ("number", "int", "bool", "object", "list", "string")


@dataclass(frozen=True)
class ParamDef:
    type: str
    required: bool = False
    default: Any = None
    doc: str = ""


@dataclass(frozen=True)
class Vocab:
    params: Dict[str, ParamDef]
    part_tags: Tuple[str, ...]
    tiled_tags: FrozenSet[str]
    big_tags: FrozenSet[str]
    no_collide_tags: FrozenSet[str]
