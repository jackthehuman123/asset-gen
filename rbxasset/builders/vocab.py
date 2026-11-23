"""Vocabulary types describing what a builder accepts. bpy-free."""

from dataclasses import dataclass
from typing import Any, Callable, Dict, FrozenSet, Optional, Tuple

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
    # optional bpy-free hook: validate(params, budgets) raises ValueError (load_spec wraps it in SpecError)
    validate: Optional[Callable[[Dict, Dict], None]] = None
    # scope, in lowercase plain words. `makes`: assets this builder produces well.
    # `not_for`: things it cannot make even if a request sounds close. No two builders
    # may share a `makes` phrase (tests/test_builder_scope.py).
    makes: Tuple[str, ...] = ()
    not_for: Tuple[str, ...] = ()
