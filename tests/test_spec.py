import copy
import json
import time
from pathlib import Path
import pytest
from rbxasset.spec import SpecError, load_spec
from rbxasset.style import load_style

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture
def style():
    return load_style(FIX / "game_STYLE.md", FIX / "area_STYLE.md")


def write(tmp_path, name, mutate):
    d = json.loads((FIX / name).read_text())
    mutate(d)
    p = tmp_path / "s.json"
    p.write_text(json.dumps(d))
    return p


def test_house_fixture_resolves(style):
    r = load_spec(FIX / "house_spec.json", style)
    assert len(r.parts) == 14 and r.finishes["kawara"]["type"] == "paint"
    assert r.to_dict()["builder"] == "house"
    c = load_spec(FIX / "cabinet_spec.json", style)
    assert len(c.decals) == 1 and "blood" not in c.wear


def test_unknown_finish_name_lists_available(style, tmp_path):
    p = write(tmp_path, "house_spec.json", lambda d: d["parts"].update(tiles_front="kawarra"))
    with pytest.raises(SpecError) as e:
        load_spec(p, style)
    assert "kawarra" in str(e.value) and "kawara" in str(e.value)


def test_unknown_param_lists_allowed(style, tmp_path):
    p = write(tmp_path, "house_spec.json", lambda d: d["params"].update(widht=3))
    with pytest.raises(SpecError) as e:
        load_spec(p, style)
    assert "widht" in str(e.value) and "width" in str(e.value)


def test_missing_part_tag_rejected(style, tmp_path):
    p = write(tmp_path, "house_spec.json", lambda d: d["parts"].pop("ridge"))
    with pytest.raises(SpecError, match="ridge"):
        load_spec(p, style)


def test_unknown_builder_rejected(style, tmp_path):
    p = write(tmp_path, "house_spec.json", lambda d: d.update(builder="castle"))
    with pytest.raises(SpecError, match="castle"):
        load_spec(p, style)


def test_finish_override_deep_merges(style, tmp_path):
    p = write(tmp_path, "house_spec.json",
              lambda d: d.update(finish_overrides={"kawara": {"color": "#000000"}}))
    r = load_spec(p, style)
    assert r.finishes["kawara"]["color"] == "#000000"
    assert r.finishes["kawara"]["roughness"] == style.finishes["kawara"]["roughness"]
    assert style.finishes["kawara"]["color"] != "#000000"


def test_bad_finish_type_rejected(style, tmp_path):
    p = write(tmp_path, "house_spec.json",
              lambda d: d.update(finish_overrides={"kawara": {"type": "glass"}}))
    with pytest.raises(SpecError, match="glass"):
        load_spec(p, style)


def test_decal_must_target_known_tag_and_kind(style, tmp_path):
    def bad(key, val):
        def m(d):
            d["decals"][0][key] = val
        return write(tmp_path, "cabinet_spec.json", m)
    with pytest.raises(SpecError, match="nope"):
        load_spec(bad("on", "nope"), style)
    with pytest.raises(SpecError, match="paint"):
        load_spec(bad("kind", "paint"), style)


def test_validation_is_fast(style):
    t = time.time()
    load_spec(FIX / "house_spec.json", style)
    assert time.time() - t < 1.0


def _house_style(tmp_path, mutate):
    return write(tmp_path, "house_spec.json", mutate)


@pytest.mark.parametrize("mutate,needle", [
    (lambda d: d["params"]["facades"].pop("back"), "back"),
    (lambda d: d["params"]["facades"].update(top=["wall"]), "top"),
    (lambda d: d["params"]["facades"]["front"].__setitem__(0, "gate"), "gate"),
    (lambda d: d["params"].update(boarded=[["front", 99]]), "out of range"),
    (lambda d: d["params"].update(boarded=[["front", 0]]), "window"),
    (lambda d: d["params"].update(door_open=[["front", 1, 0.5]]), "door"),
    (lambda d: d["params"].update(door_open=[["front", 2]]), "list of 3"),
    (lambda d: d["params"].update(boarded=[["roof", 1]]), "roof"),
])
def test_house_vocab_validate_rejects(style, tmp_path, mutate, needle):
    with pytest.raises(SpecError) as e:
        load_spec(_house_style(tmp_path, mutate), style)
    assert needle in str(e.value)


def test_house_36_wide_exceeds_tile_budget(style, tmp_path):
    p = _house_style(tmp_path, lambda d: d["params"].update(width=36))
    with pytest.raises(SpecError) as e:
        load_spec(p, style)
    assert "tiles_front" in str(e.value) and "max width" in str(e.value)
    # default-sized fixture passes
    assert load_spec(FIX / "house_spec.json", style)


def test_tile_estimate_helper_matches_builder_math():
    from rbxasset.builders.house import roof_math
    assert roof_math.estimate_tile_tris(28, 20, 30, 3.2, 1.5) < 20000
    w = roof_math.max_width(20000, 20, 30, 3.2, 1.5)
    assert roof_math.estimate_tile_tris(w, 20, 30, 3.2, 1.5) <= 20000


@pytest.mark.parametrize("mutate,needle", [
    (lambda d: d.update(finish_overrides={"kawara": 5}), "finish_overrides.kawara"),
    (lambda d: d.update(wear=[1]), "wear"),
    (lambda d: d.update(decals=[5]), "decal 0"),
    (lambda d: d.update(decals="x"), "decals"),
    (lambda d: d.update(seed="abc"), "seed"),
    (lambda d: d.update(parts=[]), "parts"),
])
def test_malformed_value_types_are_spec_errors(style, tmp_path, mutate, needle):
    with pytest.raises(SpecError) as e:
        load_spec(write(tmp_path, "house_spec.json", mutate), style)
    assert needle in str(e.value)


def test_missing_spec_file(style, tmp_path):
    with pytest.raises(SpecError, match="run `new` first"):
        load_spec(tmp_path / "nope.json", style)
