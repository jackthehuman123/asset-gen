from pathlib import Path

ROOT = Path(__file__).parent.parent
DOCS = [ROOT / "CLAUDE.md"] + sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md"))
STALE = (
    "game/STYLE.md",
    "game/areas",
    "assets/<area>",
    "<area>/<name>",
    "assets/village",
)


def test_no_stale_paths():
    for doc in DOCS:
        text = doc.read_text()
        for bad in STALE:
            # "games/<game>/STYLE.md" legitimately contains "game/STYLE.md" is not an issue: it has "games/"
            assert bad not in text.replace("games/", "G/"), "%s still mentions %s" % (
                doc.name,
                bad,
            )
