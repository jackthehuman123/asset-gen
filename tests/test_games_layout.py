import json
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
GAMES = sorted(p for p in (ROOT / "games").iterdir() if p.is_dir())


@pytest.mark.parametrize("game", GAMES, ids=lambda p: p.name)
def test_each_game_has_required_files(game):
    for name in ("STYLE.md", "CLAUDE.md", "REQUESTS.md", ".claude/settings.json"):
        assert (game / name).is_file(), "%s missing %s" % (game.name, name)


@pytest.mark.parametrize("game", GAMES, ids=lambda p: p.name)
def test_each_game_denies_siblings_and_generation(game):
    deny = json.loads((game / ".claude" / "settings.json").read_text())["permissions"]["deny"]
    for other in GAMES:
        if other != game:
            for tool in ("Read", "Edit"):
                assert "%s(../%s/**)" % (tool, other.name) in deny, (game.name, tool, other.name)
    assert "Bash(*rbxasset*)" in deny
