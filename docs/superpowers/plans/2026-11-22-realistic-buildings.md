# Realistic Buildings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ten new building types whose detail and surface realism approach the Flatiron spike (`blueprint/spike/blender/flatiron.py`), built in the normal pipeline.

**Architecture:** Two layers. (1) Finish realism: new `brick` (coursed, per-brick tone) and `siding` (clapboard) finish types and a `tile_grime` layer, so tiled walls and roofs carry real patterns. (2) Geometry realism: a shared `rbxasset/builders/arch.py` of architectural parts (walls with openings split into colour-variant panels, hooded/pedimented/arched/gothic windows, cornices with brackets and dentils, string courses, quoins, rustication, balconies, oriels, porticos, columns, awnings, storefronts, turrets, mansard frustums, half-timbering, fire escapes, soot strips under every ledge, street context). Each building is a builder package composed from it.

**Tech Stack:** Python 3.9 (vocab bpy-free), Blender bpy/bmesh, pytest.

**Spec:** the user's request: "imports were not realistic, I want the same level as the flatiron building, make 10 new building types, same pipeline, prioritize realism". What made the Flatiron look real (read from its spike): dense geometric detail, soot and colour-variant meshes chosen by geometry (tiles carry no position cues), street context.

## Global Constraints

- Units studs; ground z=0; front faces -Y; each tag under 20,000 triangles; vocab files bpy-free.
- `makes` phrases unique across builders; longer phrases shadow shorter ones across builders (matcher).
- Walls and roofs use tiled tags with `brick`/`siding` finishes; details are untiled unique bakes.
- No commits unless asked; Blender runs via `lockf .superpowers/blender.lock`.

## Review Focus

- Tall wall panels must not rotate brick courses (grain axis applies to wood only).
- Soot and colour-variant tags must exist in every building (tile finishes carry no position cues).
- A missing required finish key still fails validation, not Blender (brick/siding added to `REQUIRED_FINISH_KEYS`).
- Triangle budget: heavy buildings (warehouse, art deco) stay under 20k per tag.
- A plain "house" request still goes to `detached_house`; "japanese house" to `house`.

---

### Task 1: Finish types
Files: `rbxasset/blender/finishes.py`, `rbxasset/blender/tiling.py` (recipe 3, `use_grain`), `rbxasset/blender/executor.py`, `rbxasset/spec.py`, `docs/game-template/STYLE.md`.
- [x] `brick`: Blender Brick Texture; tiled mode uses tile UV with whole courses per tile; `brick_w`, `brick_h`, `mortar_size`; bump from the mask.
- [x] `siding`: board lines with per-board tone via white noise; `board_h`.
- [x] `tile_grime` for tiled finishes.
- [x] Required keys: brick `color_a color_b mortar`, siding `color`.

### Task 2: Architectural library
File: `rbxasset/builders/arch.py` (plus `Kit.mesh/prism/rotate_z`, `roofs.placed`).
- [x] `Face` (side plane with `box`, `rbox`, `poly`), `Op`/`win`, `wall` (panel split + colour variants), window styles plain/hooded/pediment/surround/arch/gothic, door, shop, bigdoor.
- [x] Ornament: cornice, course, quoins, rustication, balcony, oriel, column, portico, awning, chimney, balustrade, turret, frustum, fire escape, timber, gable timber, post, street context.

### Tasks 3-12: ten buildings (one package each, `makes` unique)

| Builder | Key features |
|---|---|
| brownstone | raised basement + stoop with iron rails, ashlar front, hooded windows, string courses, bracketed cornice, brick party walls, parapet |
| victorian | turret, shingled cross-gable wing, wrap porch with turned posts, side bay, steep roofs |
| tudor | plaster panels with timber studs and braces, jettied upper floor, steep gables, brick chimney |
| craftsman | front gable over a deep porch, rafter tails, tapered columns on brick piers |
| colonial_revival | symmetrical brick, shuttered windows, pedimented portico, quoins, dentil cornice, end chimneys |
| art_deco_tower | piers and dark spandrels, setbacks, portal with canopy, stepped crown and spire |
| haussmann | rusticated arched ground floor, entresol, noble floor with pediments, continuous balconies, zinc mansard with dormers |
| warehouse | pilasters, arched loft windows, loading docks with canopy, corbelled cornice, fire escape, water tank, boiler stack |
| church | buttressed nave with lancet windows, west tower with pointed doorway, belfry, spire and pinnacles |
| shopfront_block | storefronts with signboards and awnings, brick upper floors, fire escape, bracketed cornice |

Each: vocab with validation, build, registry line, a Blender contract test and a parameter-effect check (`tests/blender_scripts/new_builders_check.py`), a `/test` run with the shared city style.

### Task 13: Verify and write up
- [x] Fast suite (194), all ten `/test` builds viewed. Blender suite for the ten: see test run; findings in `blueprint/STRESS_FINDINGS.md`.
- [ ] (done above) Fast suite, Blender suite, all ten `/test` builds viewed, findings in `blueprint/STRESS_FINDINGS.md`.
