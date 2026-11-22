# nyc: build rules

This folder is one Roblox game. Your job here is building the game, nothing else.

## Sources of truth
- `STYLE.md` in this folder (look, budgets, finishes)
- `GAME.md` in this folder, if it exists
- the assets already inside this folder that you are allowed to use

## Do not
- Read or edit any other game folder (`../<other game>`). The deny rules in `.claude/settings.json` enforce this; this note explains why: other games' content is unrelated context and wastes tokens.
- Generate assets. If you need one, add an entry to `REQUESTS.md`. The creator approves each request case by case, and the pipeline agent builds it from the repo root.
