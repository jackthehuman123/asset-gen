import json
from pathlib import Path

import pytest

from rbxasset.config import ConfigError, load_config


def write_config(root: Path, **overrides) -> None:
    data = {
        "blender": "/opt/homebrew/bin/blender",
        "creator_type": "user",
        "creator_id": "123",
    }
    data.update(overrides)
    (root / "rbxasset.config.json").write_text(json.dumps(data))


def test_loads_committed_config_and_key_from_env(tmp_path, monkeypatch):
    write_config(tmp_path)
    monkeypatch.setenv("ROBLOX_API_KEY", "k")
    cfg = load_config(tmp_path)
    assert cfg.api_key == "k"
    assert cfg.creator_type == "user"


def test_key_from_dotenv_when_env_missing(tmp_path, monkeypatch):
    monkeypatch.delenv("ROBLOX_API_KEY", raising=False)
    write_config(tmp_path)
    (tmp_path / ".env").write_text("# comment\nROBLOX_API_KEY=abc\n")
    assert load_config(tmp_path).api_key == "abc"


def test_missing_key_errors_only_when_required(tmp_path, monkeypatch):
    monkeypatch.delenv("ROBLOX_API_KEY", raising=False)
    write_config(tmp_path)
    assert load_config(tmp_path).api_key is None
    with pytest.raises(ConfigError) as exc:
        load_config(tmp_path, require_key=True)
    assert "ROBLOX_API_KEY" in str(exc.value)
    assert "Creator Dashboard" in str(exc.value)


def test_creator_type_must_be_user_or_group(tmp_path):
    write_config(tmp_path, creator_type="team")
    with pytest.raises(ConfigError):
        load_config(tmp_path)


def test_creator_id_required_when_key_required(tmp_path, monkeypatch):
    monkeypatch.setenv("ROBLOX_API_KEY", "k")
    write_config(tmp_path, creator_id="")
    with pytest.raises(ConfigError) as exc:
        load_config(tmp_path, require_key=True)
    assert "creator_id" in str(exc.value)
