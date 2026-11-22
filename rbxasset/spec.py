"""Asset spec loading and fast validation against STYLE + builder vocab.

bpy-free, Python 3.9 compatible. Spec "seed" is the top-level spec key; a
house "seed" param (damage seed) defaults separately in the vocab.
"""
import copy
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List

from rbxasset.builders import REGISTRY, load_vocab
from rbxasset.style import Style

FINISH_TYPES = ("wood", "paint", "metal", "stone")
DECAL_KINDS = ("smear", "drips", "splatter")

_PY_TYPES = {
    "number": (int, float), "int": (int,), "bool": (bool,),
    "object": (dict,), "list": (list,), "string": (str,),
}
_TOP_KEYS = {"builder", "brief", "design_notes", "seed", "params", "parts",
             "finish_overrides", "wear", "decals", "area"}


class SpecError(Exception):
    pass


@dataclass
class ResolvedSpec:
    builder: str
    seed: int
    brief: str
    params: Dict
    parts: Dict[str, str]
    finishes: Dict[str, Dict]
    wear: Dict
    decals: List[Dict]

    def to_dict(self) -> Dict:
        return asdict(self)


def _names(it) -> str:
    return ", ".join(sorted(it))


def _deep_merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def _check_param(name, pdef, value):
    ok = _PY_TYPES[pdef.type]
    if isinstance(value, bool) and pdef.type != "bool":
        ok = ()
    if not isinstance(value, ok):
        raise SpecError("param '%s' must be %s, got %r" % (name, pdef.type, value))


def _vec(d, key, n, i):
    v = d.get(key)
    if not (isinstance(v, list) and len(v) == n
            and all(isinstance(x, (int, float)) for x in v)):
        raise SpecError("decal %d: '%s' must be a list of %d numbers" % (i, key, n))


def load_spec(spec_path: Path, style: Style) -> ResolvedSpec:
    spec_path = Path(spec_path)
    if not spec_path.is_file():
        raise SpecError("no spec at %s; run `new` first" % spec_path)
    try:
        raw = json.loads(spec_path.read_text(encoding="utf-8"))
    except ValueError as e:
        raise SpecError("spec is not valid JSON: %s" % e)
    if not isinstance(raw, dict):
        raise SpecError("spec must be a JSON object")
    unknown = set(raw) - _TOP_KEYS
    if unknown:
        raise SpecError("unknown spec key(s) %s; allowed: %s"
                        % (_names(unknown), _names(_TOP_KEYS)))
    builder = raw.get("builder")
    if builder not in REGISTRY:
        raise SpecError("unknown builder %r; available: %s" % (builder, _names(REGISTRY)))
    vocab = load_vocab(builder)

    for key, want in (("params", dict), ("parts", dict), ("finish_overrides", dict),
                      ("wear", dict), ("decals", list)):
        if not isinstance(raw.get(key, want()), want):
            raise SpecError("spec key '%s' must be a JSON %s, got %r"
                            % (key, "list" if want is list else "object", raw[key]))
    if "area" in raw and not isinstance(raw["area"], str):
        raise SpecError("spec key 'area' must be a string, got %r" % (raw["area"],))
    seed = raw.get("seed", 0)
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise SpecError("spec key 'seed' must be an integer, got %r" % (seed,))

    params = {}
    given = raw.get("params", {})
    for k in given:
        if k not in vocab.params:
            raise SpecError("unknown param '%s' for builder '%s'; allowed: %s"
                            % (k, builder, _names(vocab.params)))
    for k, pdef in vocab.params.items():
        if k in given:
            _check_param(k, pdef, given[k])
            params[k] = given[k]
        elif pdef.required:
            raise SpecError("missing required param '%s'" % k)
        else:
            params[k] = copy.deepcopy(pdef.default)

    finishes = copy.deepcopy(style.finishes)
    for name, over in raw.get("finish_overrides", {}).items():
        if name not in finishes:
            raise SpecError("finish_overrides names unknown finish '%s'; available: %s"
                            % (name, _names(finishes)))
        if not isinstance(over, dict):
            raise SpecError("finish_overrides.%s must be an object, got %r" % (name, over))
        finishes[name] = _deep_merge(finishes[name], over)
    for name, f in finishes.items():
        if not isinstance(f, dict):
            raise SpecError("finish '%s' must be an object, got %r" % (name, f))
        if f.get("type") not in FINISH_TYPES:
            raise SpecError("finish '%s' has bad type %r; allowed: %s"
                            % (name, f.get("type"), ", ".join(FINISH_TYPES)))

    parts = raw.get("parts", {})
    for tag in parts:
        if tag not in vocab.part_tags:
            raise SpecError("unknown part tag '%s' for builder '%s'; allowed: %s"
                            % (tag, builder, ", ".join(vocab.part_tags)))
    for tag in vocab.part_tags:
        if tag not in parts:
            raise SpecError("missing part tag '%s'; every tag needs a finish (tags: %s)"
                            % (tag, ", ".join(vocab.part_tags)))
    for tag, fname in parts.items():
        if fname not in finishes:
            raise SpecError("part '%s' uses unknown finish '%s'; available: %s"
                            % (tag, fname, _names(finishes)))

    decals = raw.get("decals", [])
    for i, d in enumerate(decals):
        if not isinstance(d, dict):
            raise SpecError("decal %d must be an object, got %r" % (i, d))
        if d.get("kind") not in DECAL_KINDS:
            raise SpecError("decal %d: bad kind %r; allowed: %s"
                            % (i, d.get("kind"), ", ".join(DECAL_KINDS)))
        if d.get("on") not in vocab.part_tags:
            raise SpecError("decal %d: 'on' %r is not a part tag; allowed: %s"
                            % (i, d.get("on"), ", ".join(vocab.part_tags)))
        _vec(d, "position", 3, i)
        _vec(d, "normal", 3, i)
        _vec(d, "size", 2, i)
        if not isinstance(d.get("color"), str):
            raise SpecError("decal %d: 'color' must be a hex string" % i)
        if not isinstance(d.get("opacity", 1.0), (int, float)):
            raise SpecError("decal %d: 'opacity' must be a number" % i)

    if vocab.validate is not None:
        try:
            vocab.validate(params, style.budgets)
        except ValueError as e:
            raise SpecError(str(e))

    wear = dict(style.wear)
    wear.update(raw.get("wear", {}))
    return ResolvedSpec(
        builder=builder, seed=seed, brief=raw.get("brief", ""),
        params=params, parts=dict(parts), finishes=finishes, wear=wear,
        decals=copy.deepcopy(decals))
