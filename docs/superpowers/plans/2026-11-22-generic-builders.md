# Generic Builders Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add eight generic builders (`table`, `chair`, `shelf`, `lamppost`, `fence`, `crate`, `barrel`, `stairs`) so the matcher stops declining everyday props, each proven by a `/test` run.

**Architecture:** Each builder is a package `rbxasset/builders/<name>/` (`vocab.py` with params, part tags, `makes`/`not_for`, `validate`; `build.py` with `build(params, rng) -> BuildResult`) registered in `REGISTRY`. A shared `rbxasset/builders/kit.py` holds the bpy primitives so builders stay small. Generic tests iterate every registered builder.

**Tech Stack:** Python 3.9 (vocab bpy-free), Blender bpy/bmesh (build), pytest.

**Spec:** `RESTRUCTURE.md` + the handover in chat ("come up with generic builder types, run /test on them, write plans, execute them all"). Pattern reference: `rbxasset/builders/phonebooth/`.

## Global Constraints

- Units: studs, about 3 studs per metre; a character is 5.5 tall. Ground at z=0, asset centred on x=0, front faces -Y.
- Max 20,000 triangles per part tag. All `vocab.py` are bpy-free.
- `makes` phrases are unique across builders and each phrase must match its own builder at `build` confidence (tested for all builders at once).
- No new finish types; glass-like parts are a separate tag with a tint finish.
- Never touch `tools/`. No commits unless asked. Blender runs go through `lockf .superpowers/blender.lock`.

## Review Focus

- Params at their limits (e.g. 1 shelf, 1 step, 2 hoops): builds, stays on the ground, under the triangle cap.
- Optional features switched off (`lid`, `arms`, `back_style: none`, `handrail`): the tag is empty, not broken.
- Bad enum strings (`leg_shape`, `picket_style`, `head_style`, `back_style`): validation error, exit 2.
- Request phrases like "phone box" or "photo booth" must not tie with `crate` or `table`.
- Matching "a coffee table" etc. returns `build` for exactly one builder.

---

### Task 1: Shared kit and generic tests

**Files:** Create `rbxasset/builders/kit.py`, `tests/blender_scripts/new_builders_check.py`, `tests/test_blender_new_builders.py`; Modify `tests/test_match.py`, `tests/test_builder_scope.py`.

**Interfaces — Produces:** `Kit(tags)` with `.parts`, `.box(tag, size, loc, rot=(0,0,0), bevel=0.01)`, `.cyl(tag, r, depth, loc, rot=(0,0,0), verts=16)`, `.cone(tag, r1, r2, depth, loc, rot=(0,0,0), verts=16)`, `.sphere(tag, r, loc, scale=(1,1,1))`, `.revolve(tag, profile, segments=24, loc=(0,0,0), closed=False)` (profile = list of `(radius, z)`; `closed=True` closes the loop for ring solids), each returning the Blender object. Generic fast test: every registered builder's every `makes` phrase matches its own builder with verdict `build`.

- [ ] Write the failing generic matcher test and the generic Blender check (`t_generic(name)`: tag set equals `vocab.part_tags`, non-empty unless the tag is in that builder's optional set, `min z` within 0.02 of 0, x-centred within 0.05, every tag under 20k triangles, shots are `(name, loc3, tgt3, lens)` with a `wide` first, `ctx` has `W` and `H`).
- [ ] Implement `kit.py` (`revolve` via `bmesh.ops.spin` plus `remove_doubles` and `recalc_face_normals`).
- [ ] Run fast suite; expected PASS (no new builders registered yet).

### Tasks 2–9: one task per builder (same steps each)

For each builder: (a) `.venv/bin/python -m rbxasset match <words>` shows `decline` (gap proven); (b) write the vocab and a failing validation test in `tests/test_new_builders_vocab.py`; (c) implement `build.py`, register it; (d) add its specific Blender assertion to `new_builders_check.py` and run `lockf ... pytest -m blender tests/test_blender_new_builders.py -k <name>`; (e) run `/test` flow: `blueprint/out_<name>/STYLE.md` (the shared everyday style), `new`, fill spec, build, look at the previews.

| Task | Builder | Params (defaults) | Tags (optional) | makes | not_for | Specific check |
|---|---|---|---|---|---|---|
| 2 | `table` | width 5.0, depth 2.8, height 2.4, top_thickness 0.16, leg_size 0.22, leg_shape "square"\|"round", apron_height 0.4, stretchers true | top, legs, apron, stretchers (apron, stretchers) | table, desk, dining table, coffee table, workbench, counter | chair, bench, shelf | top of the bbox equals `height` |
| 3 | `chair` | seat_width 1.9, seat_depth 1.8, seat_height 1.5, back_height 1.9, back_style "slats"\|"solid"\|"none", slat_count 4, leg_size 0.14, arms false | seat, legs, back, arms (back, arms) | chair, stool, bench, armchair, seat | sofa, bed, throne | `back_style: none` leaves `back` empty |
| 4 | `shelf` | width 3.6, depth 1.0, height 6.0, shelf_count 4, board_thickness 0.1, back_panel true | frame, shelves, back (back) | shelf, bookshelf, shelving unit, rack | cabinet, wardrobe, locker | `len(shelves) == shelf_count + 1` |
| 5 | `lamppost` | height 12, base_radius 0.45, base_height 1.2, pole_radius 0.14, arm_length 1.2, head_style "lantern"\|"globe", head_radius 0.45 | base, pole, arm, head, lens (arm) | lamp post, lamppost, street lamp, street light, bollard, signpost, flagpole | tree, tower, building | bbox height equals `height` |
| 6 | `fence` | length 12, height 3.4, post_spacing 4, post_size 0.3, rail_count 2, picket_width 0.32, picket_gap 0.14, picket_style "flat"\|"pointed" | posts, rails, pickets | fence, picket fence, railing, balustrade | wall, building, gate | bbox x extent equals `length` (±post) |
| 7 | `crate` | width 2.4, depth 2.0, height 1.8, board_count 4, board_thickness 0.1, batten_size 0.18, lid true | boards, battens, lid (lid) | crate, wooden crate, chest, trunk | barrel, cabinet, phone box | `lid: false` leaves `lid` empty |
| 8 | `barrel` | height 2.6, radius 1.0, bulge 0.18, hoop_count 3, wall 0.1, open_top false | body, hoops, lid (lid) | barrel, keg, cask, drum, bin, trash can | crate, tank, pipe | `open_top: true` leaves `lid` empty; hoops count equals `hoop_count` |
| 9 | `stairs` | steps 6, rise 0.55, run 0.9, width 3.0, tread_thickness 0.12, risers true, stringers true, handrail false | treads, risers, stringers, rail (rail) | stairs, staircase, stairway, steps | ladder, ramp, spiral | `len(treads) == steps`; top z equals `steps * rise` |

Validation rules (all raise `ValueError` naming the value): numeric ranges per builder, ints for counts, enum strings from the table, `post_spacing <= length`, `hoop_count >= 2`, `steps >= 1`.

### Task 10: Docs and wrap-up

**Files:** Modify `.claude/skills/asset-pipeline/SKILL.md`, `blueprint/STRESS_FINDINGS.md`; Test `tests/test_docs_paths.py` (unchanged).

- [ ] List the builders in the skill's Scope paragraph (point to `ls rbxasset/builders` as the source of truth).
- [ ] Append a table of the eight `/test` runs and how each looked (honest about weak ones).
- [ ] Run `.venv/bin/pytest -m "not blender"` and `lockf ... pytest -m blender tests/test_blender_builders.py tests/test_blender_new_builders.py`.

## Self-review

Spec coverage: eight builders (Tasks 2-9), `/test` run per builder (step e), plan (this file), generic non-overlap test (Task 1). Names consistent: `Kit.box/cyl/cone/sphere/revolve`, enum values as in the table.
