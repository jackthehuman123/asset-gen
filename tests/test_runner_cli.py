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


def make_project(tmp_path, fake_script, finish=None):
    root = tmp_path / "proj"
    (root / "game" / "areas" / "farm").mkdir(parents=True)
    shutil.copy(FIX / "game_STYLE.md", root / "game" / "STYLE.md")
    shutil.copy(FIX / "area_STYLE.md", root / "game" / "areas" / "farm" / "STYLE.md")
    fake = tmp_path / "fake_blender.sh"
    fake.write_text(fake_script.format(root=tmp_path) if "{root}" in fake_script else fake_script)
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    (root / "rbxasset.config.json").write_text(json.dumps(
        {"blender": str(fake), "creator_type": "user", "creator_id": "1"}))
    adir = root / "assets" / "farm" / "chest"
    adir.mkdir(parents=True)
    spec = json.loads((FIX / "cabinet_spec.json").read_text())
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
    mf = root / "assets" / "farm" / "chest" / "out" / "manifest.json"
    assert json.loads(mf.read_text())["asset"] == "farm/chest"
    assert (root / "assets" / "farm" / "chest" / "out" / "build.log").is_file()


def test_blender_failure_surfaces_log_tail(tmp_path):
    root, _ = make_project(tmp_path, FAKE_FAIL)
    cfg = load_config(root)
    out = root / "assets" / "farm" / "chest" / "out"
    job = {"mode": "build", "asset": "farm/chest", "out_dir": str(out),
           "manifest_path": str(out / "manifest.json")}
    with pytest.raises(BuildError) as e:
        run_blender(cfg, job)
    assert "the very last line" in str(e.value)


def test_new_scaffolds_spec_from_vocab(tmp_path):
    root, _ = make_project(tmp_path, FAKE_OK)
    assert cli.main(["new", "farm/shelf", "--builder", "cabinet"], root=root) == 0
    spec = json.loads((root / "assets" / "farm" / "shelf" / "spec.json").read_text())
    assert spec["builder"] == "cabinet" and spec["seed"] == 1
    assert set(spec["parts"]) == {"top", "carcass", "fronts", "handles", "legs", "foot_caps"}
    assert set(spec["parts"].values()) == {"TODO"}
    assert spec["params"]["width"] == 4.2


def test_sample_runs_each_variant_into_own_folder(tmp_path, capsys):
    root, log = make_project(tmp_path, FAKE_OK)
    v = tmp_path / "variants"
    v.mkdir()
    for n in ("alpha", "beta"):
        shutil.copy(FIX / "cabinet_spec.json", v / (n + ".json"))
    code = cli.main(["sample", "farm/chest", str(v / "alpha.json"), str(v / "beta.json")],
                    root=root)
    assert code == 0
    assert len(log.read_text().split()) == 2
    s = root / "assets" / "farm" / "chest" / "samples"
    assert (s / "alpha" / "manifest.json").is_file() and (s / "beta" / "manifest.json").is_file()
