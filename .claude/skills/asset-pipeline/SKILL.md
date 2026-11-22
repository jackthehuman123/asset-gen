---
name: asset-pipeline
description: Run an asset design session with the creator using the rbxasset pipeline (spec, Blender build, Open Cloud upload, Studio assembly). Use when the creator describes a house or cabinet to make, revise, or deliver to Roblox.
---

# Asset pipeline session

An asset is `<area>/<name>` (example: `village/murder_house`). Its spec lives at `assets/<area>/<name>/spec.json`. Run commands from the repo root as `.venv/bin/python -m rbxasset ...`. Exit codes: 0 ok, 2 validation or config error (fix the spec or config), 1 build or upload failure.

## Session flow

Describe -> Sample -> Lock -> Build -> Deliver.

1. Describe: the creator says what they want. Their words outrank any reference. Never invent the theme. Ask when something is unclear.
2. Sample: see below.
3. Lock: the creator picks a variant. Copy it to `spec.json` (or `.venv/bin/python -m rbxasset new <area>/<name> --builder house|cabinet` for a skeleton).
4. Build: `mkdir -p .superpowers && lockf .superpowers/blender.lock .venv/bin/python -m rbxasset build <area>/<name>`. It prints a mesh/tris table and preview paths.
5. Deliver: only after approval (below).

## Token rules

- Load only `game/STYLE.md`, the one area `game/areas/<area>/STYLE.md`, and the builder's `rbxasset/builders/<builder>/vocab.py`.
- Never read baked PNGs into context. Only open the preview images you are showing the creator.
- Revise by editing the existing spec (a small diff). Do not rewrite it.
- Game-only keys in STYLE (camera, studs_per_tile, budgets, lighting) are locked. A spec cannot set them. Lighting is one of the presets in `rbxasset/style.py`.
- The STYLE.md format is one fenced block opened with ```json style.

## Sample step

Write 2-4 variant specs that differ in finishes or params, saved anywhere (for example `assets/<area>/<name>/variants/a.json`). Run:

`mkdir -p .superpowers && lockf .superpowers/blender.lock .venv/bin/python -m rbxasset sample <area>/<name> a.json b.json c.json`

Each variant is a path, or a bare name resolved under `assets/<area>/<name>/variants/` (so `a.json` works if saved there).

Show the previews side by side and let the creator choose or mix.

## Design notes

Every spec has `design_notes`: a list of plain-words entries explaining each choice (type, walls, openings, wear, story, palette). Model them on `assets/village/murder_house/spec.json`. Update them when a revision changes a choice.

## Approval gates

- Show previews before any delivery. Never run `deliver` without the creator's explicit yes for that asset. A yes for one asset is not a yes for another.
- A rejection naming one element changes only that element. Leave everything else untouched.
- Record each rejection reason as a proposed `avoid` line in the area STYLE.md. Show it. The creator accepts it before you write it.
- When `avoid` passes 12 lines, propose a compacted version for the creator to approve.
- Blood and story marks are separate, non-graphic Decals (kinds: smear, drips, splatter). Never bake them into maps.

## Delivery

**Primary path (option A, the creator's choice on 2026-11-22):** `build` writes `out/asset.fbx` with every baked map embedded. The creator imports it with Studio's File > Import 3D, which brings in all the SurfaceAppearance maps at the right scale; the creator verified this on the spike FBXs. Story decals are not in the FBX: give the creator each decal PNG from `out/textures/` and its placement from the manifest, and they add the Decal by hand. Ask for a screenshot next to a character to check scale.

**Kept for later (option B):** automated `deliver` via Open Cloud plus `assemble.lua`. It has never run against live Roblox. The request/response shapes and the axis/scale mapping are unverified until Task 1 has run (`docs/findings/delivery.md`). Use it only when the creator asks for it, and run Task 1 first.

1. Optional check: `.venv/bin/python -m rbxasset deliver --dry-run <area>/<name>` writes the assemble script with fake ids and uploads nothing.
2. `.venv/bin/python -m rbxasset deliver <area>/<name>` (needs `ROBLOX_API_KEY` in `.env`). Uploads are cached by content hash in `roblox.json`, so a rerun re-uploads only what changed. Rejected decals are omitted. Exit 1 means upload failure, so rerun to resume.
3. Known limits: a retry after a timeout can duplicate an asset, and a crash mid-upload can orphan one. Tell the creator if either might have happened.
4. Run `out/assemble.lua` (under the asset's directory) through the Studio MCP run-code tool if connected. Otherwise ask the creator to paste it into the Command Bar.
5. Ask for a screenshot next to the character marker to check scale.

## Scope

v1 builders are `house` and `cabinet` only. For any other asset type, say a new builder is needed and that it is out of v1. Do not improvise a spec for it.

## Blender load

Wrap every Blender-running command in `lockf .superpowers/blender.lock <cmd>`. One Blender process at a time.
