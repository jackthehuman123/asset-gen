from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple


@dataclass
class AssetPaths:
    dir: Path

    @property
    def spec(self) -> Path:
        return self.dir / "spec.json"

    @property
    def out(self) -> Path:
        return self.dir / "out"

    @property
    def textures(self) -> Path:
        return self.out / "textures"

    @property
    def previews(self) -> Path:
        return self.out / "previews"

    @property
    def manifest(self) -> Path:
        return self.out / "manifest.json"

    @property
    def fbx(self) -> Path:
        return self.out / "asset.fbx"

    @property
    def assemble(self) -> Path:
        return self.out / "assemble.lua"

    @property
    def samples(self) -> Path:
        return self.dir / "samples"

    @property
    def roblox(self) -> Path:
        return self.dir / "roblox.json"


BLUEPRINT = "blueprint"
RESERVED = ("areas", "_tiles")


def split_ref(ref: str) -> Tuple[str, str]:
    parts = ref.split("/")
    if len(parts) != 2 or not all(parts) or parts[1] in RESERVED:
        raise ValueError(
            f"asset ref must be '<game>/<asset>' (asset not one of "
            f"{', '.join(RESERVED)}), got {ref!r}"
        )
    return parts[0], parts[1]


def asset_paths(root: Path, ref: str) -> AssetPaths:
    game, asset = split_ref(ref)
    if game == BLUEPRINT:
        return AssetPaths(dir=root / BLUEPRINT / f"out_{asset}")
    return AssetPaths(dir=root / "games" / game / asset)


def tiles_dir(root: Path, game: str) -> Path:
    if game == BLUEPRINT:
        return root / BLUEPRINT / "_tiles"
    return root / "games" / game / "_tiles"


def game_style_path(root: Path, game: str, asset: Optional[str] = None) -> Path:
    """Games share one STYLE.md; a blueprint test carries its own inside out_<asset>/."""
    if game == BLUEPRINT:
        return root / BLUEPRINT / f"out_{asset}" / "STYLE.md"
    return root / "games" / game / "STYLE.md"


def area_style_path(root: Path, game: str, area: str) -> Path:
    return root / "games" / game / "areas" / area / "STYLE.md"
