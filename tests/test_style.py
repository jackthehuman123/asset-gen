import json
import pytest
from rbxasset.style import StyleError, load_style, parse_style_md


def md(obj):
    return "prose\n\n```json style\n%s\n```\n" % json.dumps(obj)


def mk(tmp_path, game, area):
    g = tmp_path / "g.md"
    a = tmp_path / "a.md"
    g.write_text(md(game))
    a.write_text(md(area))
    return load_style(g, a)


def test_parse_extracts_single_json_style_block():
    assert parse_style_md('x\n```json style\n{"a": 1}\n```\ny\n```json\n{}\n```') == {
        "a": 1
    }


def test_parse_errors_on_missing_or_duplicate_block():
    with pytest.raises(StyleError):
        parse_style_md("no block")
    with pytest.raises(StyleError):
        parse_style_md(md({}) + md({}))


def test_area_overrides_finish_by_name_and_merges_wear(tmp_path):
    s = mk(
        tmp_path,
        {
            "finishes": {
                "a": {"type": "paint", "color": "#111111"},
                "b": {"type": "paint"},
            },
            "wear": {"edge": 0.1, "grime": 0.2},
        },
        {"finishes": {"a": {"type": "wood"}}, "wear": {"edge": 0.9}},
    )
    assert s.finishes["a"] == {"type": "wood"} and "b" in s.finishes
    assert s.wear == {"edge": 0.9, "grime": 0.2}


def test_area_cannot_set_locked_key(tmp_path):
    with pytest.raises(StyleError, match="camera"):
        mk(tmp_path, {}, {"camera": "third_person"})


def test_defaults_first_person_tiles_4_studs(tmp_path):
    s = mk(tmp_path, {}, {})
    assert s.camera == "first_person" and s.studs_per_tile == 4
    assert s.budgets["max_tris_per_mesh"] == 20000
    assert s.lighting == {"preset": "overcast_exterior"}
    assert mk(tmp_path, {"camera": "third_person"}, {}).studs_per_tile == 8


def test_budget_over_roblox_limit_rejected(tmp_path):
    with pytest.raises(StyleError):
        mk(tmp_path, {"budgets": {"max_tris_per_mesh": 25000}}, {})
    with pytest.raises(StyleError):
        mk(tmp_path, {"budgets": {"texture_big": 2048}}, {})


def test_avoid_lists_concatenate(tmp_path):
    assert mk(tmp_path, {"avoid": ["a"]}, {"avoid": ["b"]}).avoid == ["a", "b"]


def test_unknown_lighting_preset_rejected_with_allowed_list(tmp_path):
    with pytest.raises(StyleError) as e:
        mk(tmp_path, {"lighting": {"preset": "disco"}}, {})
    assert "disco" in str(e.value) and "abandoned_interior" in str(e.value)
    assert (
        mk(tmp_path, {"lighting": {"preset": "bright_interior"}}, {}).lighting["preset"]
        == "bright_interior"
    )


def test_malformed_budgets_and_lighting_are_style_errors(tmp_path):
    with pytest.raises(StyleError, match="budgets.max_tris_per_mesh"):
        mk(tmp_path, {"budgets": {"max_tris_per_mesh": "lots"}}, {})
    with pytest.raises(StyleError, match="budgets must be an object"):
        mk(tmp_path, {"budgets": 5}, {})
    with pytest.raises(StyleError, match="lighting"):
        mk(tmp_path, {"lighting": "dark"}, {})


def test_missing_style_file_is_style_error(tmp_path):
    g = tmp_path / "g.md"
    g.write_text(md({}))
    with pytest.raises(StyleError, match="no STYLE.md"):
        load_style(g, tmp_path / "missing.md")


def test_area_is_optional(tmp_path):
    g = tmp_path / "g.md"
    g.write_text(md({"finishes": {"a": {"type": "paint"}}, "wear": {"edge": 0.1}}))
    s = load_style(g)
    assert s.intent_area == "" and s.finishes == {"a": {"type": "paint"}}
    assert s.wear == {"edge": 0.1}
