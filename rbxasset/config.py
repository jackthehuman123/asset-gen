import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

CONFIG_FILE = "rbxasset.config.json"
ENV_FILE = ".env"
KEY_VAR = "ROBLOX_API_KEY"


class ConfigError(Exception):
    pass


@dataclass
class Config:
    root: Path
    blender: str
    creator_type: str
    creator_id: str
    api_key: Optional[str]
    open_cloud_base: str = "https://apis.roblox.com"


def _read_dotenv(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def load_config(root: Path, require_key: bool = False) -> Config:
    cfg_path = root / CONFIG_FILE
    if not cfg_path.is_file():
        raise ConfigError(f"missing {CONFIG_FILE} in {root}")
    try:
        data = json.loads(cfg_path.read_text())
    except ValueError as e:
        raise ConfigError(f"{CONFIG_FILE} is not valid JSON: {e}")
    if not isinstance(data, dict):
        raise ConfigError(f"{CONFIG_FILE} must be a JSON object")

    creator_type = str(data.get("creator_type", "user"))
    if creator_type not in ("user", "group"):
        raise ConfigError(
            f"creator_type must be 'user' or 'group', got {creator_type!r}"
        )
    creator_id = str(data.get("creator_id", ""))

    api_key = (
        os.environ.get(KEY_VAR) or _read_dotenv(root / ENV_FILE).get(KEY_VAR) or None
    )

    if require_key:
        if not api_key:
            raise ConfigError(
                f"{KEY_VAR} is not set. Export it or add it to .env. "
                "Create a key in the Roblox Creator Dashboard."
            )
        if not creator_id:
            raise ConfigError(
                f"creator_id must be set in {CONFIG_FILE} when an API key is required"
            )

    return Config(
        root=root,
        blender=str(data.get("blender", "blender")),
        creator_type=creator_type,
        creator_id=creator_id,
        api_key=api_key,
    )
