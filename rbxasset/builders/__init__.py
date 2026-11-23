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
    "brownstone": "rbxasset.builders.brownstone",
    "victorian": "rbxasset.builders.victorian",
    "tudor": "rbxasset.builders.tudor",
    "craftsman": "rbxasset.builders.craftsman",
    "colonial_revival": "rbxasset.builders.colonial_revival",
    "art_deco_tower": "rbxasset.builders.art_deco_tower",
    "haussmann": "rbxasset.builders.haussmann",
    "warehouse": "rbxasset.builders.warehouse",
    "church": "rbxasset.builders.church",
    "shopfront_block": "rbxasset.builders.shopfront_block",
}


def load_vocab(name: str) -> Vocab:
    if name not in REGISTRY:
        raise KeyError("unknown builder %r; available: %s"
                       % (name, ", ".join(sorted(REGISTRY))))
    return importlib.import_module(REGISTRY[name] + ".vocab").VOCAB
