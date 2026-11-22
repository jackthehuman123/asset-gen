These rules are for the asset pipeline. They do not apply under `tools/`, which is the creator's hand-written learning code with its own `tools/CLAUDE.md`. Never write, edit, or delete anything under `tools/`.

# rbxasset asset pipeline

The creator briefs an asset in words. You write a JSON spec, headless Blender builds it (`rbxasset`), the pipeline uploads it through Open Cloud, and an assemble script places it in Studio. To run a design session, use the skill in `.claude/skills/asset-pipeline/SKILL.md`.

## Setup

- `python3 -m venv .venv && .venv/bin/pip install pytest`
- Blender path: `rbxasset.config.json` (local, never commit it).
- `ROBLOX_API_KEY` in `.env` (needed only for a real `deliver`).

## Commands

`python -m rbxasset build|sample|new|deliver [--dry-run] <area>/<asset>`. Exit codes: 0 ok, 2 validation or config error, 1 build or upload failure.

## Tests

- Fast: `.venv/bin/pytest -m "not blender"`
- Blender: `.venv/bin/pytest -m blender`

Blender is heavy on the creator's 16GB MacBook Air. Run every Blender-running command (`build`, `sample`, `pytest -m blender`, the full suite) as `lockf .superpowers/blender.lock <cmd>`, so only one Blender process runs at a time.

## Status and rules

- Open Cloud request/response shapes and the Blender-to-Studio axis mapping are unverified until Task 1 (live delivery spike with the creator).
- Blood and story marks are separate, non-graphic Decals, never baked into maps.
- The creator's words outrank references. Never invent the theme.
- Never commit `rbxasset.config.json` or `.env`.
