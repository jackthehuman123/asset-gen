"""Builder registry. Never imports build.py (those need bpy)."""
import importlib
from typing import Dict

from rbxasset.builders.vocab import Vocab

REGISTRY: Dict[str, str] = {
    "cabinet": "rbxasset.builders.cabinet",
    "house": "rbxasset.builders.house",
}


def load_vocab(name: str) -> Vocab:
    if name not in REGISTRY:
        raise KeyError("unknown builder %r; available: %s"
                       % (name, ", ".join(sorted(REGISTRY))))
    return importlib.import_module(REGISTRY[name] + ".vocab").VOCAB
