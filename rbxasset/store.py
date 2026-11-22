from dataclasses import dataclass
from pathlib import Path


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


def asset_paths(root: Path, ref: str) -> AssetPaths:
    parts = ref.split("/")
    if len(parts) != 2 or not all(parts):
        raise ValueError(f"asset ref must be '<area>/<asset>', got {ref!r}")
    return AssetPaths(dir=root / "assets" / parts[0] / parts[1])


def tiles_dir(root: Path, area: str) -> Path:
    return root / "assets" / area / "_tiles"


def game_style_path(root: Path) -> Path:
    return root / "game" / "STYLE.md"


def area_style_path(root: Path, area: str) -> Path:
    return root / "game" / "areas" / area / "STYLE.md"
