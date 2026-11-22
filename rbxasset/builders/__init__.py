"""Builder registry. Never imports build.py (those need bpy)."""
import importlib
from typing import Dict

from rbxasset.builders.vocab import Vocab

REGISTRY: Dict[str, str] = {
    "cabinet": "rbxasset.builders.cabinet",
    "house": "rbxasset.builders.house",
    "phonebooth": "rbxasset.builders.phonebooth",
    "table": "rbxasset.builders.table",
    "chair": "rbxasset.builders.chair",
    "shelf": "rbxasset.builders.shelf",
    "lamppost": "rbxasset.builders.lamppost",
    "fence": "rbxasset.builders.fence",
    "crate": "rbxasset.builders.crate",
    "barrel": "rbxasset.builders.barrel",
    "stairs": "rbxasset.builders.stairs",
    "detached_house": "rbxasset.builders.detached_house",
    "rowhouse": "rbxasset.builders.rowhouse",
    "apartment": "rbxasset.builders.apartment",
    "cabin": "rbxasset.builders.cabin",
    "barn": "rbxasset.builders.barn",
}


def load_vocab(name: str) -> Vocab:
    if name not in REGISTRY:
        raise KeyError("unknown builder %r; available: %s"
                       % (name, ", ".join(sorted(REGISTRY))))
    return importlib.import_module(REGISTRY[name] + ".vocab").VOCAB
