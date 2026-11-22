import json
import shutil
import stat
import sys
from pathlib import Path

import pytest

from rbxasset import cli
from rbxasset.runner import BuildError, run_blender
from rbxasset.config import load_config

FIX = Path(__file__).parent / "fixtures"

FAKE_OK = """#!/bin/sh
echo invoked >> "{root}/invocations.log"
# last argv is the job json
for a; do job="$a"; done
python3 - "$job" <<'PY'
import json, sys, os
job = json.load(open(sys.argv[1]))
os.makedirs(os.path.dirname(job["manifest_path"]), exist_ok=True)
prev = os.path.join(job["out_dir"], "previews", "preview_wide.png")
os.makedirs(os.path.dirname(prev), exist_ok=True)
open(prev, "wb").write(b"x")
json.dump({{"asset": job["asset"], "mode": job["mode"], "fbx": None,
          "bounds": {{"min": [0, 0, 0], "max": [1, 1, 1]}},
          "meshes": [{{"name": "A_top", "tag": "top", "finish": "f", "tris": 12,
                      "tiled": False, "metal": False, "collide": True, "maps": {{}}}}],
          "decals": [], "previews": [prev], "bake_seconds": 0.5}},
         open(job["manifest_path"], "w"))
PY
"""

FAKE_FAIL = """#!/bin/sh
echo "line one"
echo "the very last line"
exit 1
"""


def write_variant(path):
    d = json.loads((FIX / "cabinet_spec.json").read_text())
    d["area"] = "yard"
    Path(path).write_text(json.dumps(d))


def make_project(tmp_path, fake_script, finish=None):
    root = tmp_path / "proj"
    (root / "games" / "farm" / "areas" / "yard").mkdir(parents=True)
    shutil.copy(FIX / "game_STYLE.md", root / "games" / "farm" / "STYLE.md")
    shutil.copy(FIX / "area_STYLE.md", root / "games" / "farm" / "areas" / "yard" / "STYLE.md")
    fake = tmp_path / "fake_blender.sh"
    fake.write_text(fake_script.format(root=tmp_path) if "{root}" in fake_script else fake_script)
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    (root / "rbxasset.config.json").write_text(json.dumps(
        {"blender": str(fake), "creator_type": "user", "creator_id": "1"}))
    adir = root / "games" / "farm" / "chest"
    adir.mkdir(parents=True)
    spec = json.loads((FIX / "cabinet_spec.json").read_text())
    spec["area"] = "yard"  # the fixture's finishes come from the area style
    if finish:
        spec["parts"]["top"] = finish
    (adir / "spec.json").write_text(json.dumps(spec))
    return root, tmp_path / "invocations.log"


def test_build_validates_before_blender(tmp_path, capsys):
    root, log = make_project(tmp_path, FAKE_OK, finish="no_such_finish")
    code = cli.main(["build", "farm/chest"], root=root)
    assert code == 2
    err = capsys.readouterr().err
    assert "no_such_finish" in err and "Traceback" not in err
    assert not log.exists()


def test_build_writes_manifest_and_prints_previews(tmp_path, capsys):
    root, log = make_project(tmp_path, FAKE_OK)
    code = cli.main(["build", "farm/chest"], root=root)
    assert code == 0
    out = capsys.readouterr().out
    assert "preview_wide.png" in out and "A_top" in out and "12" in out
    mf = root / "games" / "farm" / "chest" / "out" / "manifest.json"
    assert json.loads(mf.read_text())["asset"] == "farm/chest"
    assert (root / "games" / "farm" / "chest" / "out" / "build.log").is_file()


def test_blender_failure_surfaces_log_tail(tmp_path):
    root, _ = make_project(tmp_path, FAKE_FAIL)
    cfg = load_config(root)
    out = root / "games" / "farm" / "chest" / "out"
    job = {"mode": "build", "asset": "farm/chest", "out_dir": str(out),
           "manifest_path": str(out / "manifest.json")}
    with pytest.raises(BuildError) as e:
        run_blender(cfg, job)
    assert "the very last line" in str(e.value)


def test_new_scaffolds_spec_from_vocab(tmp_path):
    root, _ = make_project(tmp_path, FAKE_OK)
    assert cli.main(["new", "farm/shelf", "--builder", "cabinet"], root=root) == 0
    spec = json.loads((root / "games" / "farm" / "shelf" / "spec.json").read_text())
    assert spec["builder"] == "cabinet" and spec["seed"] == 1
    assert set(spec["parts"]) == {"top", "carcass", "fronts", "handles", "legs", "foot_caps"}
    assert set(spec["parts"].values()) == {"TODO"}
    assert spec["params"]["width"] == 4.2


def test_sample_runs_each_variant_into_own_folder(tmp_path, capsys):
    root, log = make_project(tmp_path, FAKE_OK)
    v = tmp_path / "variants"
    v.mkdir()
    for n in ("alpha", "beta"):
        write_variant(v / (n + ".json"))
    code = cli.main(["sample", "farm/chest", str(v / "alpha.json"), str(v / "beta.json")],
                    root=root)
    assert code == 0
    assert len(log.read_text().split()) == 2
    s = root / "games" / "farm" / "chest" / "samples"
    assert (s / "alpha" / "manifest.json").is_file() and (s / "beta" / "manifest.json").is_file()


def test_blender_timeout_raises_build_error(tmp_path):
    root, _ = make_project(tmp_path, "#!/bin/sh\necho started\nsleep 5\n")
    cfg = load_config(root)
    out = root / "games" / "farm" / "chest" / "out"
    job = {"mode": "build", "asset": "farm/chest", "out_dir": str(out),
           "manifest_path": str(out / "manifest.json")}
    with pytest.raises(BuildError) as e:
        run_blender(cfg, job, timeout=1)
    assert "TIMEOUT" in str(e.value)


def test_stale_manifest_removed_before_failed_build(tmp_path):
    root, _ = make_project(tmp_path, FAKE_FAIL)
    cfg = load_config(root)
    out = root / "games" / "farm" / "chest" / "out"
    out.mkdir(parents=True)
    (out / "manifest.json").write_text("{}")
    job = {"mode": "build", "asset": "farm/chest", "out_dir": str(out),
           "manifest_path": str(out / "manifest.json")}
    with pytest.raises(BuildError):
        run_blender(cfg, job)
    assert not (out / "manifest.json").exists()


def test_build_missing_spec_exits_2(tmp_path, capsys):
    root, log = make_project(tmp_path, FAKE_OK)
    assert cli.main(["build", "farm/nope"], root=root) == 2
    err = capsys.readouterr().err
    assert "run `new` first" in err and "Traceback" not in err
    assert not log.exists()


def _set_area(root, area):
    p = root / "games" / "farm" / "chest" / "spec.json"
    d = json.loads(p.read_text())
    d.pop("area", None)
    if area:
        d["area"] = area
    p.write_text(json.dumps(d))


def test_spec_area_selects_area_style(tmp_path, capsys):
    root, _ = make_project(tmp_path, FAKE_OK)
    assert cli.main(["build", "farm/chest"], root=root) == 0
    _set_area(root, None)  # no area: the area's finishes are gone
    assert cli.main(["build", "farm/chest"], root=root) == 2
    assert "stained_zelkova" in capsys.readouterr().err


def test_unknown_area_exits_2(tmp_path, capsys):
    root, _ = make_project(tmp_path, FAKE_OK)
    _set_area(root, "ghost")
    assert cli.main(["build", "farm/chest"], root=root) == 2
    assert "areas/ghost/STYLE.md" in capsys.readouterr().err


def test_missing_game_style_exits_2(tmp_path, capsys):
    root, _ = make_project(tmp_path, FAKE_OK)
    (root / "games" / "farm" / "STYLE.md").unlink()
    assert cli.main(["build", "farm/chest"], root=root) == 2
    assert "STYLE.md" in capsys.readouterr().err


def test_reserved_asset_name_exits_2(tmp_path, capsys):
    root, _ = make_project(tmp_path, FAKE_OK)
    assert cli.main(["build", "farm/areas"], root=root) == 2
    assert "Traceback" not in capsys.readouterr().err


def test_sample_bare_variant_name_resolves_under_variants(tmp_path):
    root, log = make_project(tmp_path, FAKE_OK)
    v = root / "games" / "farm" / "chest" / "variants"
    v.mkdir()
    write_variant(v / "a.json")
    assert cli.main(["sample", "farm/chest", "a.json"], root=root) == 0
    assert cli.main(["sample", "farm/chest", "missing.json"], root=root) == 2


def test_missing_config_key_exits_2(tmp_path, monkeypatch, capsys):
    root, _ = make_project(tmp_path, FAKE_OK)
    monkeypatch.delenv("ROBLOX_API_KEY", raising=False)
    out = root / "games" / "farm" / "chest" / "out"
    out.mkdir(parents=True)
    (out / "manifest.json").write_text(json.dumps({"meshes": [], "decals": []}))
    assert cli.main(["deliver", "farm/chest"], root=root) == 2
    assert "ROBLOX_API_KEY" in capsys.readouterr().err


def test_deliver_missing_map_file_exits_2(tmp_path, capsys, monkeypatch):
    root, _ = make_project(tmp_path, FAKE_OK)
    out = root / "games" / "farm" / "chest" / "out"
    out.mkdir(parents=True)
    (out / "asset.fbx").write_bytes(b"x")
    (out / "manifest.json").write_text(json.dumps({
        "fbx": str(out / "asset.fbx"), "bounds": {"min": [0, 0, 0], "max": [1, 1, 1]},
        "meshes": [{"name": "m", "collide": True, "maps": {"color": str(out / "gone.png")}}],
        "decals": []}))
    monkeypatch.setenv("ROBLOX_API_KEY", "k")

    class Stub:  # never touch the network
        def __init__(self, key, ctype, cid):
            self.creator_type, self.creator_id = ctype, cid

        def upload(self, *a):
            return "1"
    monkeypatch.setattr(cli, "OpenCloud", Stub)
    assert cli.main(["deliver", "farm/chest"], root=root) == 2


def test_upload_error_exits_1(tmp_path, monkeypatch, capsys):
    root, _ = make_project(tmp_path, FAKE_OK)
    out = root / "games" / "farm" / "chest" / "out"
    out.mkdir(parents=True)
    (out / "manifest.json").write_text(json.dumps({"meshes": [], "decals": []}))

    def boom(*a, **k):
        raise cli.UploadError("nope")
    monkeypatch.setattr(cli, "deliver_uploads", boom)
    monkeypatch.setenv("ROBLOX_API_KEY", "k")
    assert cli.main(["deliver", "farm/chest"], root=root) == 1
    assert "upload failed: nope" in capsys.readouterr().err


def _blueprint(root, with_style=True):
    d = root / "blueprint" / "out_house"
    d.mkdir(parents=True)
    shutil.copy(root / "games" / "farm" / "chest" / "spec.json", d / "spec.json")
    if with_style:
        shutil.copy(root / "games" / "farm" / "STYLE.md", d / "STYLE.md")
    return d


def test_blueprint_build_uses_per_asset_style(tmp_path):
    root, _ = make_project(tmp_path, FAKE_OK)
    d = _blueprint(root)
    spec = json.loads((d / "spec.json").read_text())
    spec.pop("area")  # a blueprint style is one file; the fixture's finishes live in it
    (d / "spec.json").write_text(json.dumps(spec))
    shutil.copy(FIX / "area_STYLE.md", d / "STYLE.md")
    assert cli.main(["build", "blueprint/house"], root=root) == 0
    assert (d / "out" / "manifest.json").is_file()


def test_blueprint_missing_style_exits_2(tmp_path, capsys):
    root, _ = make_project(tmp_path, FAKE_OK)
    _blueprint(root, with_style=False)
    assert cli.main(["build", "blueprint/house"], root=root) == 2
    assert "out_house/STYLE.md" in capsys.readouterr().err
