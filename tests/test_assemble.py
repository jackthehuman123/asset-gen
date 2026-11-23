import json
import shutil
from pathlib import Path

from rbxasset import assemble, cli

FIX = Path(__file__).parent / "fixtures"


def _manifest():
    return json.loads((FIX / "cabinet_manifest.json").read_text())


def _ids(m, skip=()):
    ids = {"/abs/assets/house/cabinet/out/asset.fbx": "111"}
    n = 200
    for mesh in m["meshes"]:
        for p in mesh["maps"].values():
            ids[p] = str(n)
            n += 1
    for d in m["decals"]:
        if d["name"] not in skip:
            ids[d["image"]] = str(n)
            n += 1
    return ids


def test_script_references_every_id_and_mesh():
    m = _manifest()
    ids = _ids(m)
    s = assemble.generate_luau(m, ids, "cabinet")
    for v in ids.values():
        assert "rbxassetid://%s" % v in s or v in s
    for mesh in m["meshes"]:
        assert mesh["name"] in s
    assert "FindFirstChildWhichIsA" in s


def test_metalness_only_for_metal_meshes():
    m = _manifest()
    s = assemble.generate_luau(m, _ids(m), "cabinet")
    assert s.count("MetalnessMap") == 1
    metal = [x for x in m["meshes"] if x["metal"]]
    for mesh in m["meshes"]:
        if not mesh["metal"]:
            assert "metalness" not in mesh["maps"]
    assert len(metal) == 2
    # metalness emitted per-mesh data only when present
    assert s.count("metalness =") == len(metal)


def test_rejected_decals_omitted():
    m = _manifest()
    s = assemble.generate_luau(m, _ids(m, skip=("blood_smear",)), "cabinet")
    assert "blood_smear" not in s
    assert "local DECALS = {\n\n}" in s


def test_to_studio_axis_mapping():
    assert assemble.to_studio([1, 2, 3]) == [1, 3, -2]


def test_missing_mesh_guard_present():
    m = _manifest()
    s = assemble.generate_luau(m, _ids(m), "cabinet")
    assert "error(" in s
    for mesh in m["meshes"]:
        assert '"%s"' % mesh["name"] in s


def test_strings_escaped():
    m = _manifest()
    s = assemble.generate_luau(m, _ids(m), 'we"ird\\name\n')
    assert 'we\\"ird\\\\name\\n' in s


def test_deliver_dry_run_writes_script_without_network(tmp_path, monkeypatch):
    a = tmp_path / "games" / "house" / "cabinet"
    (a / "out").mkdir(parents=True)
    shutil.copy(str(FIX / "cabinet_manifest.json"), str(a / "out" / "manifest.json"))
    monkeypatch.delenv("ROBLOX_API_KEY", raising=False)
    import socket

    def boom(*a, **k):
        raise AssertionError("network used")

    monkeypatch.setattr(socket, "socket", boom)
    assert cli.main(["deliver", "house/cabinet", "--dry-run"], root=tmp_path) == 0
    out = (a / "out" / "assemble.lua").read_text()
    assert "cabinet_handles" in out and "LoadAsset" in out
    first = out
    cli.main(["deliver", "house/cabinet", "--dry-run"], root=tmp_path)
    assert (a / "out" / "assemble.lua").read_text() == first


def test_missing_required_map_raises_naming_mesh_and_kind():
    import pytest

    m = _manifest()
    ids = _ids(m)
    mesh = m["meshes"][0]
    del ids[mesh["maps"]["normal"]]
    with pytest.raises(ValueError) as e:
        assemble.generate_luau(m, ids, "cabinet")
    assert mesh["name"] in str(e.value) and "normal" in str(e.value)


def test_missing_metalness_for_metal_mesh_raises():
    import pytest

    m = _manifest()
    m["meshes"][0]["metal"] = True
    with pytest.raises(ValueError, match="metalness"):
        assemble.generate_luau(m, _ids(m), "cabinet")


def test_empty_meshes_raises():
    import pytest

    m = _manifest()
    m["meshes"] = []
    with pytest.raises(ValueError, match="no meshes"):
        assemble.generate_luau(m, _ids(m), "cabinet")


def test_vertical_decal_gets_z_up_and_scale_applies():
    m = _manifest()
    d = m["decals"][0]
    d["normal"] = [0, 0, 1]  # blender +z -> studio +y
    s = assemble.generate_luau(m, _ids(m), "cabinet")
    assert "up = Vector3.zAxis" in s
    assert assemble.STUDS_PER_UNIT == 1.0
