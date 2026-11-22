import pytest

from rbxasset.store import area_style_path, asset_paths, game_style_path, tiles_dir


def test_asset_paths_layout(tmp_path):
    p = asset_paths(tmp_path, "village/headman_house")
    assert p.manifest == tmp_path / "games/village/headman_house/out/manifest.json"


def test_tiles_dir(tmp_path):
    assert tiles_dir(tmp_path, "village") == tmp_path / "games/village/_tiles"


def test_style_paths(tmp_path):
    assert game_style_path(tmp_path, "village") == tmp_path / "games/village/STYLE.md"
    assert area_style_path(tmp_path, "village", "x") == tmp_path / "games/village/areas/x/STYLE.md"


def test_bad_ref_rejected(tmp_path):
    for ref in ("house", "a/b/c", "village/areas", "village/_tiles"):
        with pytest.raises(ValueError):
            asset_paths(tmp_path, ref)


def test_blueprint_paths(tmp_path):
    assert asset_paths(tmp_path, "blueprint/house").dir == tmp_path / "blueprint/out_house"
    assert tiles_dir(tmp_path, "blueprint") == tmp_path / "blueprint/_tiles"
    assert game_style_path(tmp_path, "blueprint", "house") == tmp_path / "blueprint/out_house/STYLE.md"
