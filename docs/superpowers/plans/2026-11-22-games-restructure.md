# Games Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the single `game/` + `assets/<area>/` layout with `games/<game>/` folders (own STYLE.md, CLAUDE.md, REQUESTS.md, assets), add a `blueprint/` test lane, and add `/make` and `/test` entry points.

**Architecture:** An asset ref changes from `<area>/<asset>` to `<game>/<asset>`. `store.py` resolves everything under `games/<game>/`; `blueprint/<asset>` is a special game whose asset dir is `blueprint/out_<asset>/` and whose STYLE.md sits inside that dir. The old area style layer survives as an optional `games/<game>/areas/<area>/STYLE.md`, selected by an optional `"area"` key in the spec. Isolation between games = per-game `.claude/settings.json` deny rules (enforced) + per-game `CLAUDE.md` (explains), pinned by a consistency test.

**Tech Stack:** Python 3.9 (bpy-free modules), pytest, Claude Code skills and settings.

**Spec:** `RESTRUCTURE.md` (repo root). Out of scope: the Blender template, the memory investigation, `/test` agent mode, GAME.md contents, Studio setup. No Blender process runs in this plan.

## Global Constraints

- Never write, edit or delete anything under `tools/`.
- `rbxasset/style.py`, `store.py`, `spec.py`, `cli.py` stay bpy-free and Python 3.9 compatible.
- CLI exit codes: 0 ok, 2 validation/config error, 1 build/upload failure.
- Fast tests: `.venv/bin/pytest -m "not blender"`. Do not run Blender tests.
- Do not commit unless the creator asks. Never commit `.env`.
- Calls made by the planner (not the creator): optional `"area"` spec key selects the area style; reserved names inside a game dir are `areas`, `_tiles`; blueprint ref `blueprint/<name>` maps to dir `blueprint/out_<name>`.

## Review Focus

- A ref with 1 or 3 parts, or an asset named `areas`/`_tiles`: exit 2, no traceback.
- Spec names an `"area"` that has no STYLE.md: exit 2, message names the missing path.
- A game folder with no `STYLE.md`: exit 2, message names the path.
- Area STYLE.md setting a locked key (camera, budgets, ...) still fails.
- A new game added to `games/` without deny rules for its siblings (or siblings without a deny for it): the layout test fails.

---

### Task 1: Core layout (store, style, spec, cli)

**Files:**
- Modify: `rbxasset/store.py`, `rbxasset/style.py`, `rbxasset/spec.py`, `rbxasset/cli.py`
- Test: `tests/test_store.py`, `tests/test_style.py`, `tests/test_spec.py`, `tests/test_runner_cli.py`, `tests/test_blender_build_e2e.py` (fixture paths only)

**Interfaces:**
- Produces (`store.py`):
  - `RESERVED = ("areas", "_tiles")`
  - `split_ref(ref: str) -> Tuple[str, str]` raises `ValueError("asset ref must be '<game>/<asset>', got ...")` unless exactly two non-empty parts and asset not in `RESERVED`
  - `asset_paths(root, ref) -> AssetPaths` with dir `games/<game>/<asset>`
  - `tiles_dir(root, game) -> Path` = `games/<game>/_tiles`
  - `game_style_path(root, game) -> Path` = `games/<game>/STYLE.md`
  - `area_style_path(root, game, area) -> Path` = `games/<game>/areas/<area>/STYLE.md`
- Produces (`style.py`): `load_style(game_md: Path, area_md: Optional[Path] = None) -> Style`; with `None`, area keys contribute nothing and `intent_area == ""`.
- Produces (`spec.py`): `"area"` is an allowed top-level key (must be a string if present); `ResolvedSpec` is unchanged.
- Produces (`cli.py`): `_load(root, ref, spec_path)` reads the raw spec's optional `"area"` (ignore unreadable JSON; `load_spec` reports it) and builds the style from the game file plus that area file.

- [ ] **Step 1: Write failing tests**

`tests/test_store.py`: `test_asset_paths_layout` (`asset_paths(root, "village/headman_house").manifest == root/"games/village/headman_house/out/manifest.json"`); `test_tiles_dir` (`== root/"games/village/_tiles"`); `test_style_paths` (`game_style_path(root,"village") == root/"games/village/STYLE.md"`, `area_style_path(root,"village","x") == root/"games/village/areas/x/STYLE.md"`); `test_bad_ref_rejected` over `"house"`, `"a/b/c"`, `"village/areas"`, `"village/_tiles"` (each raises `ValueError`).

`tests/test_style.py`: `test_area_is_optional` — `load_style(game_file)` returns a Style whose `intent_area == ""` and whose finishes equal the game's.

`tests/test_spec.py`: `test_area_key_allowed` — a valid spec with `"area": "farm"` loads; `"area": 3` raises `SpecError` mentioning `area`.

`tests/test_runner_cli.py`: change `make_project` to lay out `games/farm/STYLE.md`, `games/farm/areas/yard/STYLE.md` (from `FIX/game_STYLE.md`, `FIX/area_STYLE.md`) and the asset at `games/farm/chest/spec.json`; update all `"farm/chest"`-style paths and `root / "assets" / "farm"` to `root / "games" / "farm"`. Add `test_spec_area_selects_area_style` (spec with `"area": "yard"` → `cli.main(["build","farm/chest"], root=root) == 0`; without `"area"` → also 0), `test_unknown_area_exits_2` (spec `"area": "ghost"` → exit 2, stderr contains `areas/ghost/STYLE.md`), `test_missing_game_style_exits_2` (delete `games/farm/STYLE.md` → exit 2, stderr contains `STYLE.md`). Replace `test_unknown_area_style_exits_2`.

`tests/test_blender_build_e2e.py`: move the `game/...` fixture paths to `games/farm/...` and the asset dir to `games/farm/<asset>`, and add `"area": "farm"` to its spec if it relied on the area file. (Marked `blender`; edited but not run.)

- [ ] **Step 2: Run** `.venv/bin/pytest -m "not blender" tests/test_store.py tests/test_style.py tests/test_spec.py tests/test_runner_cli.py -q` — Expected: FAIL.
- [ ] **Step 3: Implement** the interfaces above. `load_style` skips the locked-key check and area merges when `area_md is None`. `cli._load` raises `StyleError("no STYLE.md for area '<a>' at <path>")` when the named area file is missing, and `StyleError("no STYLE.md for game '<g>' at <path>")` when the game file is missing (via `_read`'s existing message is acceptable if it names the path). Update `cmd_build`/`cmd_sample` to pass `store.tiles_dir(root, game)` with `game = store.split_ref(ref)[0]`, and `cmd_deliver` to use `store.split_ref(ref)[1]` for the model name.
- [ ] **Step 4: Run** the same command plus `.venv/bin/pytest -m "not blender" -q` — Expected: all PASS.

---

### Task 2: Migrate data to `games/`

**Files:**
- Move: `game/STYLE.md` → `games/village/STYLE.md`; `game/areas/village/` → `games/village/areas/village/`; `assets/village/murder_house`, `assets/village/murder_house_console`, `assets/village/_tiles` → `games/village/`; `worlds/nyc` → `games/nyc`
- Modify: `games/village/murder_house/spec.json`, `games/village/murder_house_console/spec.json` (add `"area": "village"`), `.gitignore`

**Interfaces:** Consumes Task 1 layout. Produces a tree where `village/murder_house` and `village/murder_house_console` resolve and validate.

- [ ] **Step 1: Move** with plain `mv` (ignored `out/` and `_tiles/` dirs must travel with them), then remove the empty `game/`, `assets/`, `worlds/` dirs.
- [ ] **Step 2: Edit** both village specs to add `"area": "village"`; replace the `.gitignore` lines `assets/**/out/`, `assets/**/samples/`, `assets/**/_tiles/` with `games/**/out/`, `games/**/samples/`, `games/**/_tiles/`, and add `blueprint/out_*/`.
- [ ] **Step 3: Verify** both specs validate without Blender:
  `.venv/bin/python -c "from pathlib import Path; from rbxasset import cli, store; r=Path('.'); [cli._load(r, a, store.asset_paths(r, a).spec) for a in ('village/murder_house','village/murder_house_console')]"` — Expected: no output, exit 0. Then `git status --short` shows no `out/` or `_tiles/` files.
- [ ] **Step 4: Note** that `out/manifest.json` and `roblox.json` hold absolute old paths; they are regenerated by the next build (not run here).

---

### Task 3: Per-game CLAUDE.md, REQUESTS.md, deny rules

**Files:**
- Create: `docs/game-template/CLAUDE.md`, `docs/game-template/REQUESTS.md`, `games/village/CLAUDE.md`, `games/nyc/CLAUDE.md`, `games/village/REQUESTS.md`, `games/nyc/REQUESTS.md`, `games/village/.claude/settings.json`, `games/nyc/.claude/settings.json`
- Test: `tests/test_games_layout.py`

**Interfaces:** Produces the rule that every directory `games/<g>/` contains `STYLE.md`, `CLAUDE.md`, `REQUESTS.md` and `.claude/settings.json`, and that settings `permissions.deny` contains `Read(../<s>/**)` and `Edit(../<s>/**)` for every sibling game `<s>`, plus `Bash(*rbxasset*)`.

- [ ] **Step 1: Write failing tests** in `tests/test_games_layout.py`: `test_each_game_has_required_files` and `test_each_game_denies_siblings_and_generation`, both parametrized over `sorted(p for p in (ROOT/"games").iterdir() if p.is_dir())` (use a module-level list; skip nothing).
- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_games_layout.py -q` — Expected: FAIL.
- [ ] **Step 3: Write files.**
  - `CLAUDE.md` (game): purpose is building this game only. Sources of truth: this game's `STYLE.md`, `GAME.md` (if present) and assets listed as allowed. Never read or edit another game's folder. Never generate assets: add an entry to `REQUESTS.md` instead; the creator approves case by case and the pipeline agent fulfils it from the repo root.
  - `REQUESTS.md` template: statuses `pending | approved | built | rejected`; entry shape `## <asset> — <status>` with bullets `Need`, `Where used`, `Style notes`, `Result` (pipeline fills: output path, or the creator's rejection reason; rejected = built but not good enough by human judgement).
  - `.claude/settings.json`: `{"permissions": {"deny": [...]}}` with the denies above.
- [ ] **Step 4: Run** the test and `.venv/bin/pytest -m "not blender" -q` — Expected: PASS.
- [ ] **Step 5: Flag to the creator:** nested-settings loading and the `../` pattern syntax are unverified in this harness. Check by starting a session in `games/village/` and trying to read `../nyc/STYLE.md`.

---

### Task 4: `/make` skill, updated pipeline skill, root CLAUDE.md

**Files:**
- Create: `.claude/skills/make/SKILL.md`
- Modify: `.claude/skills/asset-pipeline/SKILL.md`, `CLAUDE.md` (root; not `tools/`)
- Test: `tests/test_docs_paths.py`

**Interfaces:** Consumes `<game>/<asset>` refs. Produces `/make <game> <asset>`.

- [ ] **Step 1: Write failing test** `test_no_stale_paths`: reads `CLAUDE.md`, `.claude/skills/*/SKILL.md`; asserts none contains `game/STYLE.md`, `game/areas`, `assets/<area>` or `<area>/<name>`.
- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_docs_paths.py -q` — Expected: FAIL.
- [ ] **Step 3: Edit.** `make/SKILL.md`: arguments `<game> <asset>`; load only `games/<game>/STYLE.md`, `games/<game>/GAME.md` if it exists, the matching `REQUESTS.md` entry, the optional area style named by the spec, and the builder vocab; then follow the asset-pipeline flow with ref `<game>/<asset>`; on rejection record the reason in the `REQUESTS.md` entry and propose an `avoid` line. In `asset-pipeline/SKILL.md` and root `CLAUDE.md` replace every `<area>/<name>` with `<game>/<asset>`, paths with `games/<game>/...`, and the token rule with the games paths; mention the `blueprint/` lane and per-game isolation in root `CLAUDE.md`.
- [ ] **Step 4: Run** the test and the fast suite — Expected: PASS.

---

### Task 5: `/test` lane (blueprint)

**Files:**
- Modify: `rbxasset/store.py`, `rbxasset/cli.py`
- Create: `.claude/skills/test/SKILL.md`
- Test: `tests/test_store.py`, `tests/test_runner_cli.py`

**Interfaces:**
- Consumes: Task 1 store/cli.
- Produces: `store.BLUEPRINT = "blueprint"`. For game `blueprint`: `asset_paths(root, "blueprint/<n>").dir == root/"blueprint"/f"out_{n}"`; `tiles_dir(root, "blueprint") == root/"blueprint/_tiles"`; `game_style_path(root, "blueprint", asset: Optional[str] = None)` returns `root/"blueprint"/f"out_{asset}"/"STYLE.md"` (signature gains the optional `asset`; other games ignore it). `cli._load` passes the asset name.

- [ ] **Step 1: Write failing tests:** `test_blueprint_paths` (the three values above); `test_blueprint_build_uses_per_asset_style` (project with `blueprint/out_house/{STYLE.md,spec.json}` copied from fixtures, fake Blender OK → `cli.main(["build","blueprint/house"], root=root) == 0`); `test_blueprint_missing_style_exits_2` (no STYLE.md → exit 2, stderr contains `out_house/STYLE.md`).
- [ ] **Step 2: Run** the two test files — Expected: FAIL.
- [ ] **Step 3: Implement** the branch in `store.py` and pass `asset` from `cli._load`. `/test` skill: `/test <asset> <style>`; human mode only: the creator fills `blueprint/out_<asset>/STYLE.md` (and a spec), the skill runs `build blueprint/<asset>` under the lock. Agent mode (REQUESTS.md-driven) is deferred; say so in the skill.
- [ ] **Step 4: Run** `.venv/bin/pytest -m "not blender" -q` — Expected: all PASS.

---

## Self-review

- Coverage: games layout (T1–T2), per-game STYLE/CLAUDE/REQUESTS/deny (T3), `/make` (T4), `/test` human mode + `out_<asset>` + gitignore (T2, T5), failure = rejected (T3, T4). Deferred as stated at the top: Blender template, memory, GAME.md, agent-mode `/test`, Studio.
- Names consistent: `split_ref`, `tiles_dir(root, game)`, `game_style_path(root, game, asset=None)`, `area_style_path(root, game, area)`, `load_style(game_md, area_md=None)`.
- Execution: native recommended (five small tasks sharing one store interface, no Blender).
