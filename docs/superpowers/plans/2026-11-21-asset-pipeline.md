# Roblox Asset Pipeline (v1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A terminal-driven pipeline that turns a creator's brief into a themed, game-ready Roblox asset (house exteriors and furniture) and delivers it into Studio automatically.

**Architecture:** A pure-Python package `rbxasset` (CLI, STYLE.md + spec loading and validation, Open Cloud upload, Luau assembly generation) drives headless Blender through one entry script. Inside Blender, builder modules turn a validated spec into tagged parts. A shared executor applies named finishes from STYLE.md, bakes unique maps for detailed parts and seamless tiles for large surfaces, renders previews, and exports FBX plus a manifest. The AI agent (Claude Code) is the designer: it writes and revises specs and STYLE.md, guided by a project skill. Everything after the spec is deterministic scripts.

**Tech Stack:** Python 3.9 stdlib (CLI side, no third-party runtime deps), pytest (dev), Blender 5.3 headless (bundled Python 3.13, `bpy`, Cycles on the Metal GPU), Roblox Open Cloud Assets API, Luau (Studio assembly script).

**Spec:** `docs/superpowers/specs/2026-11-21-asset-pipeline-design.md` (background and spike log: `blueprint/`, spike code: `blueprint/spike/blender/`)

## Global Constraints

- 20,000 triangles max per MeshPart; exceeding it is a build error, never a Studio surprise.
- Texture maps max 1024×1024; texture sizes: 1024 for big tags, 512 for small tags.
- SurfaceAppearance maps: Color, Normal (OpenGL / tangent space), Roughness, Metalness (metalness only for metal finishes).
- 1 Blender unit = 1 stud; a character is ~5.5 studs tall.
- Default camera is first-person (players 1–2 studs from walls) → large flat surfaces use seamless tiles; detailed parts keep unique bakes.
- Blood and story marks are separate, non-graphic Decal assets, never baked into an asset's maps.
- The creator's own words outrank references; the pipeline never invents the theme.
- AI does design only (specs, STYLE.md, revisions). Build, bake, render, upload, and assembly are scripts.
- The Open Cloud API key never goes into a committed file (env var `ROBLOX_API_KEY` or gitignored `.env`).
- The CLI-side code must run on the system Python 3.9 (no `match`, use `typing.Optional`/`Dict`), and Blender-side code runs on Blender's Python. Modules imported by both sides must stay 3.9-compatible and bpy-free.

## Review Focus

1. **Re-delivering after a small spec change** must not re-upload unchanged files or create duplicate Roblox assets (content-hash cache in `roblox.json`). Test: Task 10.
2. **Upload interrupted mid-house** (network error, 429, moderation rejection of one image out of ~45): saved progress must let a rerun continue from where it stopped. A rejected *decal* must not block the asset; a rejected *mesh/texture* must stop it with a clear message. Test: Task 10.
3. **A typo'd finish name or unknown builder parameter in a spec** must fail in under a second with the offending name and the allowed names, before a multi-minute Blender run. Test: Task 3.
4. **A mesh over 20k triangles** must fail the build and name the tag and count. Test: Task 6.
5. **Missing API key, or creator ID set to user while the game is group-owned** (401/403 from Open Cloud) must produce an actionable error before or at the first upload, not a stack trace. Test: Task 2 (missing key) and Task 10 (401/403).

---

## File Structure

```
rbxasset.config.json            # committed: blender path, creator_type, creator_id
.env                             # gitignored: ROBLOX_API_KEY=...
pyproject.toml                   # pytest config, markers
rbxasset/
  __init__.py
  __main__.py                    # python -m rbxasset → cli.main()
  cli.py                         # build | sample | deliver | new
  config.py                      # Config, load_config
  store.py                       # AssetPaths, path helpers
  style.py                       # STYLE.md parsing + layering
  spec.py                        # spec loading + validation → ResolvedSpec
  runner.py                      # run_blender(job) → manifest
  upload.py                      # Open Cloud client + cached, resumable delivery
  assemble.py                    # manifest + ids → Luau assembly script
  builders/
    __init__.py                  # REGISTRY, load_vocab
    vocab.py                     # Vocab, ParamDef (pure)
    cabinet/vocab.py  cabinet/build.py
    house/vocab.py    house/build.py
  blender/                       # imported only inside Blender
    entry.py                     # blender -b -P entry.py -- job.json
    finishes.py                  # make_finish (object or tile mode)
    tiling.py                    # bake_tile, tile_uvs
    executor.py                  # join_parts, bake_meshes, swap_to_baked, export_fbx
    preview.py                   # lighting presets, render_shots
    decals.py                    # render_decal
game/STYLE.md                    # game-wide style (creator-owned)
game/areas/village/STYLE.md      # area style
assets/<area>/<asset>/spec.json  # + out/, samples/, roblox.json
assets/<area>/_tiles/            # shared seamless tiles per finish
.claude/skills/asset-pipeline/SKILL.md   # how the agent runs a session
CLAUDE.md
tests/ (pytest; tests/blender_scripts/*.py run inside Blender via tests/blender_harness.py)
spike/delivery/                  # Task 1 throwaway
docs/findings/delivery.md        # Task 1 output
```

---

### Task 1: Delivery verification spike (with the creator)

Throwaway. It settles spec §7 risk #1 before any delivery code is written. **Needs the creator:** an Open Cloud API key with Assets read+write, their user or group ID (whoever owns the game), and Studio open on a test place.

**Files:**
- Create: `spike/delivery/upload_spike.py`, `spike/delivery/assemble_spike.lua`
- Create: `docs/findings/delivery.md`

- [ ] **Step 1: Write `upload_spike.py`** (stdlib `urllib`, multipart by hand). It uploads `blueprint/spike/blender/out_styled/cabinet_styled.fbx` re-exported **without** embedded textures as `assetType: "Model"`, and `Cabinet_oak_color.png` + `Cabinet_oak_normal.png` as `assetType: "Decal"`. Intended API: `POST https://apis.roblox.com/assets/v1/assets` with header `x-api-key`, multipart fields `request` (JSON: `assetType`, `displayName`, `description`, `creationContext.creator.userId|groupId`) and `fileContent`. Then poll `GET https://apis.roblox.com/assets/v1/operations/{id}` until `done`, and read `response.assetId` and `response.moderationResult`. Print everything raw.
- [ ] **Step 2: Run it.** Run: `ROBLOX_API_KEY=... python3 spike/delivery/upload_spike.py --user|--group <id>`. Expected: 3 asset IDs printed. Record the raw responses.
- [ ] **Step 3: Write `assemble_spike.lua`** for the Studio command bar. It calls `InsertService:LoadAsset(modelId)` and lists the MeshParts, their names, `MeshPart.Size`, and the triangle count if available. It resolves each decal ID to its image via `InsertService:LoadAsset(decalId):FindFirstChildWhichIsA("Decal").Texture`, creates a `SurfaceAppearance` on `Cabinet_oak` with `ColorMap`/`NormalMap`, and places the model next to a 2×5.5×1 marker.
- [ ] **Step 4: Run it in Studio with the creator** (paste into the command bar, or run via the Studio MCP server's run-code tool if the creator has it connected). Ask the creator to screenshot the result.
- [ ] **Step 5: Test UV tiling.** Set the oak MeshPart's UVs outside 0..1. Re-export a 4×4-stud plane with UVs 0..4 as `tile_test.fbx`, upload it, apply the color map, and confirm the texture **repeats** rather than clamps.
- [ ] **Step 6: Write `docs/findings/delivery.md`** answering each of these with evidence:
  - Exact working request and response shapes, plus the Decal→image-ID path.
  - Are triangle counts preserved (Cabinet_oak should be 996)?
  - Is the imported size in studs (W 4.2 × H 3.0)?
  - Mapping from Blender coords to Studio coords for decal placement (expected `(x, y, z)_blender → (x, z, -y)_studio`).
  - Can SurfaceAppearance maps be set from the command bar, and from MCP?
  - Do UVs outside 0..1 repeat?
  - Moderation state field names.
  - Which Studio mechanism to use: MCP run-code if available, else command-bar paste.

  If any answer contradicts the intended path in spec §5.4, stop and bring it to the creator before Task 10.
- [ ] **Step 7: Commit** (after Task 2 has run `git init`, or include `git init` here)

```bash
git add spike/delivery docs/findings/delivery.md
git commit -m "spike: verify Open Cloud upload + Studio assembly path"
```

---

### Task 2: Repo scaffold, config, and paths

**Files:**
- Create: `.gitignore`, `pyproject.toml`, `rbxasset.config.json`, `rbxasset/__init__.py`, `rbxasset/__main__.py`, `rbxasset/config.py`, `rbxasset/store.py`, `tests/test_config.py`, `tests/test_store.py`, `tests/blender_harness.py`

**Interfaces:**
- Produces:
  - `config.Config(root: Path, blender: str, creator_type: str, creator_id: str, api_key: Optional[str], open_cloud_base: str = "https://apis.roblox.com")`
  - `config.load_config(root: Path, require_key: bool = False) -> Config`
  - `config.ConfigError(Exception)`
  - `store.AssetPaths` (dataclass, field `dir: Path`; properties `spec`, `out`, `textures`, `previews`, `manifest`, `fbx`, `assemble`, `samples`, `roblox` → `dir/"spec.json"`, `dir/"out"`, `out/"textures"`, `out/"previews"`, `out/"manifest.json"`, `out/"asset.fbx"`, `out/"assemble.lua"`, `dir/"samples"`, `dir/"roblox.json"`)
  - `store.asset_paths(root: Path, ref: str) -> AssetPaths` (`ref` = `"<area>/<asset>"`)
  - `store.tiles_dir(root: Path, area: str) -> Path` (`root/"assets"/area/"_tiles"`)
  - `store.game_style_path(root) -> Path` (`root/"game"/"STYLE.md"`), `store.area_style_path(root, area) -> Path` (`root/"game"/"areas"/area/"STYLE.md"`)
  - `tests/blender_harness.run_blender_script(script: str, *args: str) -> subprocess.CompletedProcess` (runs `blender -b --factory-startup --python-exit-code 1 --python tests/blender_scripts/<script> -- *args` and asserts return code 0, printing the last 60 log lines on failure)

- [ ] **Step 1: Scaffold.** Run `git init`, and create a venv: `python3 -m venv .venv && .venv/bin/pip install pytest`. `.gitignore` covers `.venv/`, `.env`, `assets/**/out/`, `assets/**/samples/`, `assets/**/_tiles/`, `__pycache__/`, `blueprint/spike/blender/out*/`, `*.log`. `pyproject.toml` registers pytest marker `blender: runs headless Blender (slow)`. `rbxasset.config.json`: `{"blender": "/opt/homebrew/bin/blender", "creator_type": "user", "creator_id": ""}`.
- [ ] **Step 2: Write failing tests** `tests/test_config.py`:
  - `test_loads_committed_config_and_key_from_env` (tmp root with config JSON + `monkeypatch.setenv("ROBLOX_API_KEY","k")` → `cfg.api_key == "k"`, `cfg.creator_type == "user"`)
  - `test_key_from_dotenv_when_env_missing` (`.env` containing `ROBLOX_API_KEY=abc` → `"abc"`)
  - `test_missing_key_errors_only_when_required` (`load_config(root)` ok with `api_key is None`; `load_config(root, require_key=True)` raises `ConfigError` whose message contains `"ROBLOX_API_KEY"` and `"Creator Dashboard"`)
  - `test_creator_type_must_be_user_or_group` (`"team"` → `ConfigError`)
  - `test_creator_id_required_when_key_required` (empty `creator_id` + `require_key=True` → `ConfigError` mentioning `creator_id`)

  `tests/test_store.py`:
  - `test_asset_paths_layout` (`asset_paths(root, "village/headman_house").manifest == root/"assets/village/headman_house/out/manifest.json"`)
  - `test_bad_ref_rejected` (`"house"` and `"a/b/c"` → `ValueError`)
- [ ] **Step 3: Run** `.venv/bin/pytest tests/test_config.py tests/test_store.py -v`. Expected: FAIL (modules missing).
- [ ] **Step 4: Implement** `config.py` and `store.py` per the Interfaces. `.env` parsing: `KEY=VALUE` lines, `#` comments ignored.
- [ ] **Step 5: Run the tests again.** Expected: PASS.
- [ ] **Step 6: Commit** `git add -A && git commit -m "feat: scaffold rbxasset package, config, asset paths"`

---

### Task 3: STYLE.md and spec loading with validation

**Files:**
- Create: `rbxasset/style.py`, `rbxasset/spec.py`, `rbxasset/builders/__init__.py`, `rbxasset/builders/vocab.py`, `rbxasset/builders/cabinet/__init__.py`, `rbxasset/builders/cabinet/vocab.py`, `rbxasset/builders/house/__init__.py`, `rbxasset/builders/house/vocab.py`, `tests/test_style.py`, `tests/test_spec.py`, `tests/fixtures/` (game + area STYLE.md, house + cabinet specs)

**Interfaces:**
- Produces:
  - `style.StyleError(Exception)`; `style.parse_style_md(text: str) -> dict`, which extracts exactly one fenced block opened with ` ```json style `
  - `style.Style` dataclass: `intent_game: str, intent_area: str, camera: str, studs_per_tile: float, budgets: Dict, lighting: Dict, palette: Dict, finishes: Dict[str, Dict], wear: Dict, avoid: List[str]`
  - `style.load_style(game_md: Path, area_md: Path) -> Style`
  - `builders.vocab.ParamDef(type: str, required: bool = False, default: Any = None, doc: str = "")` (`type` ∈ `"number"|"int"|"bool"|"object"|"list"|"string"`)
  - `builders.vocab.Vocab(params: Dict[str, ParamDef], part_tags: Tuple[str, ...], tiled_tags: FrozenSet[str], big_tags: FrozenSet[str], no_collide_tags: FrozenSet[str])`
  - `builders.REGISTRY: Dict[str, str]` = `{"cabinet": "rbxasset.builders.cabinet", "house": "rbxasset.builders.house"}`; `builders.load_vocab(name: str) -> Vocab`
  - `spec.SpecError(Exception)`; `spec.FINISH_TYPES = ("wood", "paint", "metal", "stone")`; `spec.DECAL_KINDS = ("smear", "drips", "splatter")`
  - `spec.ResolvedSpec` dataclass: `builder: str, seed: int, brief: str, params: Dict, parts: Dict[str, str], finishes: Dict[str, Dict], wear: Dict, decals: List[Dict]`, plus `to_dict() -> Dict`
  - `spec.load_spec(spec_path: Path, style: Style) -> ResolvedSpec`

Spec file shape (pinned): `{"builder", "brief", "design_notes": [..], "seed": int, "params": {..}, "parts": {tag: finish_name}, "finish_overrides": {finish_name: {partial}}, "wear": {..}, "decals": [{"kind", "color", "on": tag, "position": [x,y,z], "normal": [x,y,z], "size": [w,h], "opacity"}]}`. Port the spike specs into this shape for fixtures: `house_abandoned_japanese.json` (`house` + `damage` → `params`; `finishes` → the area fixture STYLE.md) and `tv_console_abandoned_japanese.json`. The house vocab params are exactly the spike's `house` + `damage` keys; the cabinet vocab params are `width, depth, leg_height, body_height, drawer_column_width` with spike defaults `4.2, 1.6, 0.55, 2.45, 1.4`. Part tags: house = the 14 tags in the spike spec `parts`; cabinet = `top, carcass, fronts, handles, legs, foot_caps`. House tiled tags: `siding, plaster, roof_base, foundation, gable`. House big tags (unique-baked at 1024): `frame, engawa, tiles_front, tiles_back`. House no-collide tags: `lattice, tiles_front, tiles_back, ridge, eaves`. Cabinet: no tiled tags; big = `carcass, fronts`; no-collide = `handles, foot_caps`.

Layering rules (pinned):
- `LOCKED_KEYS = ("camera", "studs_per_tile", "budgets", "lighting")`. These are game-only, and an area defining one raises `StyleError` naming the key.
- `finishes`: union, with the area winning per name. `wear`, `palette`: shallow merge, area wins. `avoid`: game + area concatenated.
- Defaults: `camera="first_person"`, `studs_per_tile` = 4 (first_person) / 8 (third_person), `budgets={"max_tris_per_mesh": 20000, "texture_big": 1024, "texture_small": 512}`, `lighting={"preset": "overcast_exterior"}`.
- `max_tris_per_mesh > 20000` or a texture size > 1024 raises `StyleError`.

- [ ] **Step 1: Write failing tests** `tests/test_style.py`:
  - `test_parse_extracts_single_json_style_block`
  - `test_parse_errors_on_missing_or_duplicate_block`
  - `test_area_overrides_finish_by_name_and_merges_wear`
  - `test_area_cannot_set_locked_key` (area sets `"camera"` → `StyleError` with `"camera"` in the message)
  - `test_defaults_first_person_tiles_4_studs`
  - `test_budget_over_roblox_limit_rejected` (`max_tris_per_mesh: 25000` → `StyleError`)
  - `test_avoid_lists_concatenate`
- [ ] **Step 2: Write failing tests** `tests/test_spec.py`:
  - `test_house_fixture_resolves` (14 parts; `finishes["kawara"]["type"] == "paint"`)
  - `test_unknown_finish_name_lists_available` (part → `"kawarra"` → `SpecError` whose message contains `"kawarra"` and `"kawara"`)
  - `test_unknown_param_lists_allowed` (`params.widht` → `SpecError` containing `"widht"` and `"width"`)
  - `test_missing_part_tag_rejected` (drop `"ridge"` → `SpecError` containing `"ridge"`)
  - `test_unknown_builder_rejected`
  - `test_finish_override_deep_merges` (override `kawara.color` only; `roughness` is kept from the style)
  - `test_bad_finish_type_rejected` (`"type": "glass"`)
  - `test_decal_must_target_known_tag_and_kind`
  - `test_validation_is_fast` (`load_spec` on the house fixture < 1.0 s)
- [ ] **Step 3: Run** `.venv/bin/pytest tests/test_style.py tests/test_spec.py -v`. Expected: FAIL.
- [ ] **Step 4: Implement** `style.py`, `builders/vocab.py`, the two `vocab.py` modules, `builders/__init__.py`, and `spec.py` per the Interfaces and pinned rules. The defaults of params with `required=False` get filled in.
- [ ] **Step 5: Run** the same command. Expected: PASS.
- [ ] **Step 6: Commit** `git commit -am "feat: STYLE.md layering and validated asset specs"` (add new files first)

---

### Task 4: Finish library in Blender (object mode) with wear fixes

**Files:**
- Create: `rbxasset/blender/__init__.py`, `rbxasset/blender/finishes.py`, `tests/blender_scripts/finishes_check.py`, `tests/test_blender_finishes.py`

**Interfaces:**
- Consumes: finish dicts and wear dicts as resolved in Task 3.
- Produces: `finishes.FinishNodes = namedtuple("FinishNodes", "mat sockets bsdf out")` (`sockets` has keys `color`, `roughness`, `metalness`); `finishes.make_finish(name: str, finish: Dict, wear: Dict, ctx: Dict, tile: Optional[float] = None) -> FinishNodes`; `finishes.lin(hex: str) -> Tuple[float, float, float, float]`.

Port `make_finish` from `blueprint/spike/blender/lib_pipeline.py`, keeping its four types, its wear layers (water_stains, streaks, grime, edge, moss, dust), `skip_wear`, and per-axis grain from the `grain` attribute. **Remove the blood layer** (blood becomes decals in Task 8). Visual fixes from spec §7 #4:
- **Dust:** must read as a fine, even film. Use a high-frequency mask (noise scale ≥ 20) multiplied by the up-facing mask, with no large-scale patches. The large patch mask from the spike is what read as mold.
- **Plaster ("paint" with `"mottle"` key):** add optional `"mottle"` (0–1) for low-frequency discoloration and `"cracks"` (0–1) for thin dark Voronoi-edge lines. The village plaster gets both.

`tile` is accepted but ignored until Task 5 (the signature is fixed now).

- [ ] **Step 1: Write failing test** `tests/test_blender_finishes.py::test_finishes_build_and_render` (marker `blender`). It runs `finishes_check.py`, which for each of the 4 types plus a wood with every wear layer creates a cube, applies `make_finish`, bakes a 64² color map via EMIT, and asserts:
  - the baked pixels are not constant (std > 0.01);
  - a metal finish has metalness mean > 0.5;
  - a `stone` finish's color differs between mortar and cell samples.
- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_blender_finishes.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** `finishes.py`.
- [ ] **Step 4: Run** the same command. Expected: PASS.
- [ ] **Step 5: Commit** `git commit -m "feat: finish library (wood/paint/metal/stone + wear) in Blender"`

---

### Task 5: Seamless tiles for large surfaces

**Files:**
- Create: `rbxasset/blender/tiling.py`, `tests/blender_scripts/tiling_check.py`, `tests/test_blender_tiling.py`
- Modify: `rbxasset/blender/finishes.py` (tile mode)

**Interfaces:**
- Consumes: `make_finish(..., tile=S)`.
- Produces:
  - `tiling.bake_tile(finish_name: str, finish: Dict, wear: Dict, studs: float, res: int, out_dir: str) -> Dict[str, str]` (kind → PNG path; files named `<finish_name>_<kind>.png`; reuses existing files whose sibling `<finish_name>.hash` matches a hash of `(finish, wear, studs, res)`)
  - `tiling.tile_uvs(obj, studs: float) -> None`

**Tile mode in `make_finish`** (when `tile=S`): all noise and Voronoi coordinates come from the bake plane's UV `(u, v)` in [0, 1), mapped onto a 4D torus so the texture is periodic:

```
a = 2π·u, b = 2π·v
vec = (Rx·cos a, Rx·sin a, Ry·cos b),  w = Ry·sin b     # 4D noise / Voronoi
Rx = S·sx/(2π), Ry = S·sy/(2π)    # sx, sy = the axis scales the object-mode recipe used for that noise
```

For wood, the grain axis is U. Layers that need geometry or position (`grime`, `edge`, `moss`'s up/low/crevice terms, `dust`) are skipped in tile mode. Noise-only terms (streaks, water stains, the patchy part of moss) stay.

**`tile_uvs`** gives each face planar UVs = world coordinates / `studs` on the two axes perpendicular to its dominant normal axis. For faces whose `grain` attribute axis lies in that plane, U follows the grain axis.

- [ ] **Step 1: Write failing tests** `tests/test_blender_tiling.py` (marker `blender`), run via `tiling_check.py`:
  - `test_tile_is_seamless`: bake a 256² wood tile and a 256² stone tile. The mean absolute difference between column 0 and column 255, and between row 0 and row 255, must be < 0.02 (0–1 range), compared with the mean difference between adjacent interior columns × 3.
  - `test_tile_uvs_scale`: a 12×1×8 box with `studs=4` gets UV extents of 3.0 (±0.01) along 12 and 2.0 along 8.
  - `test_tile_uvs_follow_grain`: a vertical board (0.45×0.12×4, grain=Z) gets U spanning 1.0 and V spanning 0.1125 on its front face.
  - `test_tile_cache_reused`: a second `bake_tile` call with the same inputs returns in < 1 s and doesn't rewrite the files (mtime unchanged).
- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_blender_tiling.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** tile mode in `finishes.py`, plus `tiling.py`.
- [ ] **Step 4: Run** the same command. Expected: PASS.
- [ ] **Step 5: Commit** `git commit -m "feat: seamless finish tiles and grain-aware tiled UVs"`

---

### Task 6: Executor: join, budget guard, bake, export

**Files:**
- Create: `rbxasset/blender/executor.py`, `tests/blender_scripts/executor_check.py`, `tests/test_blender_executor.py`

**Interfaces:**
- Consumes: `make_finish`, `bake_tile`, `tile_uvs`, `Vocab` tag sets.
- Produces:
  - `executor.BudgetError(Exception)` (message: `"<prefix>_<tag>: <n> triangles > <max>"`)
  - `executor.MeshInfo` dataclass: `obj, name: str, tag: str, finish: str, tris: int, tiled: bool, metal: bool, collide: bool, maps: Dict[str, str]`
  - `executor.join_parts(parts: Dict[str, list], spec: Dict, vocab_sets: Dict[str, List[str]], style: Dict, ctx: Dict, prefix: str) -> List[MeshInfo]`. One mesh per tag, with `grain` tagged before joining. Tiled tags get `tile_uvs`; others get Smart UV (66°, margin 0.01). Raises `BudgetError` when `tris > style["budgets"]["max_tris_per_mesh"]`.
  - `executor.bake_meshes(meshes: List[MeshInfo], tex_dir: str, tiles_dir: str, spec: Dict, style: Dict, samples: int = 32) -> float`. Unique meshes bake color/roughness/normal (+ metalness if metal) at `texture_big` for big tags and `texture_small` otherwise. Tiled meshes get `maps` pointing at `bake_tile` outputs (shared per finish). Uses the Metal GPU when available, CPU otherwise. Returns seconds.
  - `executor.swap_to_baked(meshes: List[MeshInfo]) -> None`
  - `executor.export_fbx(meshes: List[MeshInfo], path: str) -> None` (no embedded textures; `axis_forward="-Z"`, `axis_up="Y"`, `apply_scale_options="FBX_SCALE_UNITS"`)

Port from `lib_pipeline.py`. Keep the spike fixes (the module-level `scene` bug, bmesh bisect for sag stays in the house builder).

- [ ] **Step 1: Write failing tests** `tests/test_blender_executor.py` (marker `blender`):
  - `test_join_one_mesh_per_tag_with_finish`: two tags, three cubes → 2 meshes named `T_a`, `T_b`.
  - `test_budget_guard_names_tag`: a tag whose parts total 21k tris (subdivided plane) → `BudgetError` whose message contains `"T_big"` and `"21`.
  - `test_bake_sizes_and_metalness`: a big tag gives a 1024² color map, a small tag gives 512², a metal finish gets a metalness map, wood gets none.
  - `test_tiled_tag_uses_shared_tile`: two tiled tags with the same finish have identical `maps["color"]` paths under `tiles_dir`.
  - `test_export_fbx_exists_and_reimports_with_same_tris`: re-import the FBX in a fresh scene; triangle counts per object match.
- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_blender_executor.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** `executor.py`.
- [ ] **Step 4: Run** the same command. Expected: PASS.
- [ ] **Step 5: Commit** `git commit -m "feat: executor with triangle budget guard, unique+tiled bakes, FBX export"`

---

### Task 7: Builders (cabinet, house with kawara fix)

**Files:**
- Create: `rbxasset/builders/cabinet/build.py`, `rbxasset/builders/house/build.py`, `tests/blender_scripts/builders_check.py`, `tests/test_blender_builders.py`

**Interfaces:**
- Consumes: `params` dict (validated, defaults filled), `random.Random(seed)`.
- Produces: `build(params: Dict, rng: random.Random) -> BuildResult`, where `BuildResult = namedtuple("BuildResult", "parts shots ctx")`:
  - `parts: Dict[str, List[bpy.types.Object]]` keyed by the vocab's part tags;
  - `shots: List[Tuple[str, Tuple[float, float, float], Tuple[float, float, float], float]]` as `(name, cam_location, target, lens)`;
  - `ctx = {"W": float, "H": float}`.

  The house must produce shots named `wide`, `front`, `close_opening`, `roof`; the cabinet produces `wide`, `close`. Both put the asset's ground at z=0, centered on x/y.

Port geometry from `blueprint/spike/blender/cabinet_styled.py` and `house.py`, keeping the roof sag with bmesh bisect and the capped eave tiles.

**Kawara fix:** each tile column alternates a **pan** row (concave channel: a half-cylinder, open side up, radius 0.3, placed in the slab) and a **cover** row (convex half-cylinder, radius 0.16) seated over the joint between pans. Spacing is 0.6 per pan+cover pair. Damage (missing/slipped) applies per segment to both. Name objects `pan_*` and `cover_*`.

- [ ] **Step 1: Write failing tests** `tests/test_blender_builders.py` (marker `blender`):
  - `test_house_deterministic`: the house fixture params with seed 13, built twice, give the same object count per tag.
  - `test_house_all_tags_present_and_under_budget`: every vocab tag has ≥1 part, and the joined tris per tag are < 20000.
  - `test_house_has_pan_and_cover_tiles`: `tiles_front` has both `pan_*` and `cover_*` objects, with counts within 15% of each other.
  - `test_house_roof_sags`: the max z of ridge-tag vertices near x=0 is lower than near x=±W/2 by ≥ 0.5×`roof_sag`.
  - `test_house_openings_are_open`: a ray cast from outside through the center of a front `window` bay at sill+1 hits no `plaster`/`siding` part before y=0.
  - `test_cabinet_dimensions_follow_params`: width 5.4 / body 1.55 / legs 0.45 give a bounding box of 5.48 ± 0.02 wide and 2.0 ± 0.02 tall.
  - `test_shots_named`
- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_blender_builders.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** both builders.
- [ ] **Step 4: Run** the same command. Expected: PASS.
- [ ] **Step 5: Commit** `git commit -m "feat: cabinet and house builders (pan+cover kawara)"`

---

### Task 8: Story decals, previews, Blender entry, and build CLI

**Files:**
- Create: `rbxasset/blender/decals.py`, `rbxasset/blender/preview.py`, `rbxasset/blender/entry.py`, `rbxasset/runner.py`, `rbxasset/cli.py`, `tests/test_runner_cli.py`, `tests/test_blender_build_e2e.py`

**Interfaces:**
- Consumes: Tasks 3–7.
- Produces:
  - `decals.render_decal(kind: str, color: str, seed: int, res: int, path: str) -> str` (RGBA PNG built with `mathutils.noise`; transparent background; non-graphic: muted, dried tone, no anatomical shapes)
  - `preview.PRESETS = ("bright_interior", "abandoned_interior", "overcast_exterior")` (values from the spikes: white room/area light 900 W; dim plaster + tatami, cold area 500 W + warm point 25 W; ground plane + sky 0.9 + sun 1.6). `preview.render_shots(shots, preset: str, out_dir: str, samples: int, res: Tuple[int, int], bounds) -> List[str]`, which always adds a 2×5.5×1 grey character marker beside the asset.
  - `entry.py` reads a job JSON: `{"mode": "build"|"sample", "spec": ResolvedSpec.to_dict(), "style": {"studs_per_tile", "budgets", "lighting"}, "vocab": {"tiled_tags", "big_tags", "no_collide_tags"}, "asset": str, "out_dir", "tiles_dir", "manifest_path"}`.
    - `build` mode runs: builder → join → bake → swap → decals → export → previews.
    - `sample` mode runs: builder → join → procedural materials (no bake) → previews at 800×600, 24 samples.
    - It writes the manifest and exits nonzero on any exception.
  - **Manifest** (pinned keys):

    ```
    {"asset", "mode", "fbx": path|null, "bounds": {"min": [x,y,z], "max": [x,y,z]},
     "meshes": [{"name", "tag", "finish", "tris", "tiled", "metal", "collide", "maps": {kind: path}}],
     "decals": [{"name", "image", "on", "position", "normal", "size", "opacity"}],
     "previews": [path], "bake_seconds": float}
    ```

    Coordinates are Blender coordinates; conversion happens in Task 11.
  - `runner.BuildError(Exception)`; `runner.run_blender(cfg: Config, job: Dict, timeout: int = 3600) -> Dict` (invokes `[cfg.blender, "-b", "--factory-startup", "--python-exit-code", "1", "--python", <entry.py>, "--", <job.json>]`; on failure raises with the last 60 log lines; the log is saved to `out/build.log`)
  - CLI: `python -m rbxasset build <area>/<asset>`; `python -m rbxasset sample <area>/<asset> <variant.json> [<variant.json> ...]` (each variant is a spec, and previews go to `samples/<variant-stem>/`); `python -m rbxasset new <area>/<asset> --builder <name>` (writes `spec.json` with vocab defaults, every part tag mapped to `"TODO"`, `seed: 1`).

    Each command prints the preview paths and, for build, a table of mesh / tris / tiled. Validation (Task 3) runs before Blender starts.

- [ ] **Step 1: Write failing tests** `tests/test_runner_cli.py` (fast, Blender replaced by a fake executable script that writes a canned manifest):
  - `test_build_validates_before_blender` (spec with a bad finish → exit code 2 and the `SpecError` text; the fake Blender is never invoked)
  - `test_build_writes_manifest_and_prints_previews`
  - `test_blender_failure_surfaces_log_tail` (fake exits 1 → `BuildError` containing the fake's last log line)
  - `test_new_scaffolds_spec_from_vocab`
  - `test_sample_runs_each_variant_into_own_folder`
- [ ] **Step 2: Write failing test** `tests/test_blender_build_e2e.py::test_cabinet_build_end_to_end` (marker `blender`). It runs the real build on the cabinet fixture in a tmp asset dir and asserts:
  - the manifest has 6 meshes, all tris < 20000;
  - every non-tiled mesh has color/roughness/normal map files;
  - the `handles` mesh has metalness;
  - the FBX exists, and ≥ 2 previews exist;
  - a decal in the fixture spec yields an RGBA PNG whose corner pixel alpha == 0.
- [ ] **Step 3: Run** `.venv/bin/pytest tests/test_runner_cli.py tests/test_blender_build_e2e.py -v`. Expected: FAIL.
- [ ] **Step 4: Implement** `decals.py`, `preview.py`, `entry.py`, `runner.py`, `cli.py`, `__main__.py`.
- [ ] **Step 5: Run** the same command. Expected: PASS.
- [ ] **Step 6: Commit** `git commit -m "feat: build/sample/new CLI, Blender entry, previews, story decals"`

---

### Task 9: Village STYLE.md, real specs, and the house build check

**Files:**
- Create: `game/STYLE.md`, `game/areas/village/STYLE.md`, `assets/village/murder_house/spec.json`, `assets/village/murder_house_console/spec.json`

Content comes from the creator's decisions and the spikes:
- **Game STYLE.md:**
  - intent: horror game in an abandoned Japanese village where a murder happened in one house five years ago, in the creator's words from `blueprint/01-vision.md`;
  - `camera: "first_person"`, `lighting: {"preset": "overcast_exterior"}`;
  - default budgets.
- **Village STYLE.md:**
  - `finishes` = the seven house finishes plus `stained_zelkova`, `stained_zelkova_fronts`, `forged_iron` from the spike specs, with plaster `mottle: 0.5, cracks: 0.3`;
  - `wear` = the house wear;
  - `avoid: ["too clean", "saturated colors", "modern trim"]`.
- **Specs:** the two spike specs ported to the Task 3 shape. The console gets one `smear` decal on the top-left front edge (from the spike's blood region), muted color `#3A1A14`, opacity 0.7.

- [ ] **Step 1: Run** `.venv/bin/python -m rbxasset build village/murder_house`. Expected: exit 0; 14 meshes listed, each < 20000 tris, `tiled = yes` for siding/plaster/roof_base/foundation/gable; 4 previews printed.
- [ ] **Step 2: Run** `.venv/bin/python -m rbxasset build village/murder_house_console`. Expected: exit 0; 6 meshes, 1 decal.
- [ ] **Step 3: Visual check.** Open the previews, look at them yourself, and compare against the blueprint spike renders. Kawara must read as pan + cover tiles rather than logs, plaster must show mottling and cracks, and dust must read as a film rather than mold. Then show the creator `wide` + `close_opening` + `roof` for approval. Record their verdict in `assets/village/murder_house/NOTES.md`. If they reject an element, adjust the spec or finish and rerun before continuing.
- [ ] **Step 4: Commit** `git add game assets && git commit -m "feat: village STYLE.md and murder house + console specs"`

---

### Task 10: Open Cloud upload with cache and resume

**Files:**
- Create: `rbxasset/upload.py`, `tests/test_upload.py`

**Interfaces:**
- Consumes: Task 1 findings (`docs/findings/delivery.md`), which are authoritative for request/response shapes. The shapes below are the intended path from spec §5.4.
- Produces:
  - `upload.UploadError(Exception)`; `upload.ModerationRejected(UploadError)` (has `.path`)
  - `upload.OpenCloud(api_key: str, creator_type: str, creator_id: str, base_url: str = "https://apis.roblox.com", poll_interval: float = 1.0, max_polls: int = 120)`
    - `.upload(path: Path, asset_type: str, display_name: str) -> str` (asset ID); `asset_type` ∈ `"Model"|"Decal"`
  - `upload.deliver_uploads(manifest: Dict, paths: AssetPaths, client: OpenCloud) -> Dict[str, str]` (file path → asset ID)
    - Uploads the FBX as `Model`, and every unique map and decal PNG as `Decal`.
    - Caches in `roblox.json` as `{"files": {"<sha256>": {"id", "type", "name", "rejected": bool}}}`, which is rewritten after **each** upload.
    - A file whose hash is cached is skipped.

**Behavior:**
- 401/403 → `UploadError` with the message `"Open Cloud rejected the API key or creator. Check ROBLOX_API_KEY has Assets read+write and creator_type/creator_id match the game's owner (user vs group)."`
- 429 / 5xx → retry with exponential backoff (1, 2, 4, 8, 16 s), then `UploadError`.
- A rejected decal is recorded as `rejected: true` and skipped, and the run continues.
- A rejected map or FBX → `ModerationRejected` (after saving the cache).

- [ ] **Step 1: Write failing tests** `tests/test_upload.py` with a local `http.server` fake on a thread, whose behavior is scripted per test:
  - `test_upload_polls_operation_until_done` (returns the ID from `response.assetId`; the request has `x-api-key` and multipart `request` JSON with `creationContext.creator.groupId` when `creator_type="group"`)
  - `test_auth_failure_message_mentions_user_vs_group` (403 → message contains `"user vs group"`)
  - `test_429_retries_then_succeeds` (patch sleep)
  - `test_redeliver_skips_cached_files` (2nd run → 0 requests)
  - `test_changed_file_reuploads_only_that_file`
  - `test_resume_after_crash` (fake fails on the 3rd upload with 500×6 → `UploadError`; `roblox.json` holds 2 entries; rerun uploads only the remaining files)
  - `test_rejected_decal_does_not_block` (decal rejected → recorded, returns IDs for the rest)
  - `test_rejected_texture_raises_after_saving_cache`
- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_upload.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** `upload.py` (stdlib `urllib.request`, hand-built multipart).
- [ ] **Step 4: Run** the same command. Expected: PASS.
- [ ] **Step 5: Commit** `git commit -m "feat: cached, resumable Open Cloud uploads"`

---

### Task 11: Studio assembly script and `deliver` command

**Files:**
- Create: `rbxasset/assemble.py`, `tests/test_assemble.py`
- Modify: `rbxasset/cli.py` (add `deliver`)

**Interfaces:**
- Consumes: manifest (Task 8), `deliver_uploads` (Task 10), the coordinate mapping from Task 1 findings (default `(x, y, z) → (x, z, -y)`).
- Produces:
  - `assemble.to_studio(v: List[float]) -> List[float]`
  - `assemble.generate_luau(manifest: Dict, ids: Dict[str, str], asset_name: str) -> str`
  - CLI `python -m rbxasset deliver <area>/<asset> [--dry-run]`. It loads config with `require_key=True` unless `--dry-run`, uploads, and writes `out/assemble.lua`. It prints its path plus: *"Run it via the Studio MCP run-code tool, or paste it into Studio's Command Bar."* `--dry-run` uses fake IDs and makes no network calls.

**Generated Luau must:**
1. `InsertService:LoadAsset(<modelId>)`, and take the Model inside.
2. Resolve each decal asset ID to its image via `LoadAsset(decalId):FindFirstChildWhichIsA("Decal").Texture`, caching per ID.
3. For each manifest mesh, find the MeshPart by name, set `Anchored = true` and `CanCollide = collide`, and add a `SurfaceAppearance` with ColorMap/NormalMap/RoughnessMap (and MetalnessMap if present). Tiled meshes use their tile maps.
4. For each non-rejected decal, create an anchored, transparent, non-colliding 0.05-thick Part at `to_studio(position)`, facing `to_studio(normal)`, sized `size`, with a `Decal` (Front face, `Transparency = 1 - opacity`).
5. Name the Model `asset_name`, set `WorldPivot` to the bottom center of its bounding box, parent it to `workspace`, select it, and print `"<asset_name>: <n> meshes, <m> decals"`.
6. Fail loudly (`error(...)`) if any manifest mesh is missing from the loaded model.

- [ ] **Step 1: Write failing tests** `tests/test_assemble.py`:
  - `test_script_references_every_id_and_mesh`
  - `test_metalness_only_for_metal_meshes`
  - `test_rejected_decals_omitted`
  - `test_to_studio_axis_mapping` (`[1, 2, 3] → [1, 3, -2]`)
  - `test_missing_mesh_guard_present` (the script contains `error(` and every mesh name in its expected list)
  - `test_deliver_dry_run_writes_script_without_network` (CLI on the cabinet fixture manifest)
- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_assemble.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** `assemble.py` and the `deliver` subcommand.
- [ ] **Step 4: Run** `.venv/bin/pytest -m "not blender" -v`. Expected: all PASS.
- [ ] **Step 5: Commit** `git commit -m "feat: Studio assembly script generation and deliver command"`

---

### Task 12: Agent skill, CLAUDE.md, and the end-to-end acceptance session

**Files:**
- Create: `.claude/skills/asset-pipeline/SKILL.md`, `CLAUDE.md`, `docs/findings/acceptance.md`

**SKILL.md must cover:**
- **Session flow** (spec §5.1): Describe → Sample → Lock → Build → Deliver. The creator's words outrank references; never invent the theme.
- **Token rules** (spec §5.3):
  - Load only `game/STYLE.md`, the one area STYLE.md, and the builder's `vocab.py`.
  - Never read baked PNGs into context except the preview images being shown.
  - Revise by editing the existing spec (a small diff).
- **Approval gates:**
  - Show previews before any delivery, and never run `deliver` without the creator's explicit yes for that asset.
  - A rejection naming one element changes only that element.
  - Record each reason as a proposed `avoid` line in the area STYLE.md, which the creator accepts.
  - When `avoid` passes 12 lines, propose a compacted version.
- **Sample step:** write 2–4 variant specs that differ in finishes/params, run `rbxasset sample`, and show the previews side by side.
- **Design notes:** every spec has `design_notes` explaining the choices in plain words, like the spike specs.
- **Delivery:**
  - Run `rbxasset deliver`.
  - Then run `out/assemble.lua` through the Studio MCP run-code tool if connected, otherwise ask the creator to paste it into the Command Bar.
  - Ask for a screenshot next to the character marker.
- **Scope:** v1 builders are `house` and `cabinet` only. For other asset types, say a new builder is needed (out of v1).

**CLAUDE.md** must open with this scoping line, verbatim: *"These rules are for the asset pipeline. They do not apply under `tools/`, which is the creator's hand-written learning code with its own `tools/CLAUDE.md`. Never write, edit, or delete anything under `tools/`."* It then covers setup (`python3 -m venv .venv && .venv/bin/pip install pytest`; Blender path in `rbxasset.config.json`; `ROBLOX_API_KEY` in `.env`), test commands (`.venv/bin/pytest -m "not blender"`, `.venv/bin/pytest -m blender`), and a pointer to the skill.

- [ ] **Step 1: Write** SKILL.md and CLAUDE.md.
- [ ] **Step 2: Run the full suite** `.venv/bin/pytest -v`. Expected: all PASS.
- [ ] **Step 3: Acceptance with the creator.** Run `python -m rbxasset deliver village/murder_house` and `python -m rbxasset deliver village/murder_house_console`, then run both assembly scripts in their test place. Check spec §5.5 together:
  - correct scale next to a 5.5-stud character;
  - every MeshPart has all its maps;
  - ≤ 20k tris per mesh;
  - pivot on the ground and sensible collision;
  - no visible blur from 1–2 studs on walls (tiles) and on detailed parts;
  - the console's decal is present and removable.
- [ ] **Step 4: Rerun** `deliver` on the house after changing one finish color in the spec. Confirm only the affected tile/maps re-upload (Review Focus #1).
- [ ] **Step 5: Write `docs/findings/acceptance.md`** with the checklist results, screenshots, and anything the creator rejected, each as a follow-up.
- [ ] **Step 6: Commit** `git add -A && git commit -m "docs: agent skill, CLAUDE.md, v1 acceptance"`
