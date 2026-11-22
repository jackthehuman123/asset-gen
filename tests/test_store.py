import pytest

from rbxasset.store import asset_paths


def test_asset_paths_layout(tmp_path):
    root = tmp_path
    p = asset_paths(root, "village/headman_house")
    assert p.manifest == root / "assets/village/headman_house/out/manifest.json"


def test_bad_ref_rejected():
    for ref in ("house", "a/b/c"):
        with pytest.raises(ValueError):
            asset_paths(None, ref)
