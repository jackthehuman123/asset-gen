These rules are for the asset pipeline. They do not apply under `tools/`, which is the creator's hand-written learning code with its own `tools/CLAUDE.md`. Never write, edit, or delete anything under `tools/`.

# rbxasset asset pipeline

The creator briefs an asset in words. You write a JSON spec, headless Blender builds it (`rbxasset`), the pipeline uploads it through Open Cloud, and an assemble script places it in Studio. To run a design session, use the skill in `.claude/skills/asset-pipeline/SKILL.md`.

## Setup

- `python3 -m venv .venv && .venv/bin/pip install pytest`
- `rbxasset.config.json` is committed. It holds the blender path, `creator_type` and `creator_id`, and no secrets.
- `ROBLOX_API_KEY` in `.env` (needed only for a real `deliver`).

## Commands

`.venv/bin/python -m rbxasset build|sample|new|deliver [--dry-run] <area>/<asset>`. Exit codes: 0 ok, 2 validation or config error, 1 build or upload failure.

## Tests

- Fast: `.venv/bin/pytest -m "not blender"`
- Blender: `.venv/bin/pytest -m blender`

Blender is heavy on the creator's 16GB MacBook Air. Run every Blender-running command (`build`, `sample`, `pytest -m blender`, the full suite) as `mkdir -p .superpowers && lockf .superpowers/blender.lock <cmd>` (the lock file lives in `.superpowers/`), so only one Blender process runs at a time.

## Status and rules

- Delivery: the main path is the FBX with embedded maps, imported through Studio's File > Import 3D (creator-verified). The Open Cloud `deliver` command is kept for later. Its request/response shapes and axis mapping are unverified until Task 1 (live delivery spike with the creator).
- Blood and story marks are separate, non-graphic Decals, never baked into maps.
- The creator's words outrank references. Never invent the theme.
- Never commit `.env` (the only secret).
