# Stress test, 2026-11-22 (blueprint lane)

Each test is `blueprint/out_<name>/{STYLE.md,spec.json,out/previews/}`. Peak memory per build: 1.7-2.7 GB (whole `lockf` run).

| Test | Builder | Style ask | Result |
|---|---|---|---|
| scandi_sideboard | cabinet | pale oak, matt white, brass, bright interior | Reads as Scandinavian mid-century. Style alone changed the era completely. |
| steel_locker | cabinet | painted steel, NYC service room | Shape stays a low-console-style cabinet stretched tall (drawers + doors), not a locker. `paint` with `mottle: 0.12` reads as marble, not paint. The `wide` preview is cropped tight on a tall asset. |
| whitewash_house | house | whitewash, terracotta, blue shutters, undamaged | Reads as a half-timbered cottage. Form is still Japanese (engawa, lattice, hip-gable). Setting every damage param to 0 gives a clean house. |
| minimal_sideboard | cabinet | scandi finishes cut to type + 1-2 colours | Near-identical to the full version, ~70% less style text. |

## What this says
1. STYLE.md controls look (colour, material, wear, lighting), never form. Form is builder + params.
2. Only a few finish keys are required; the rest default. Required: wood `base`+`grain`; paint `color`; metal `color`; stone `color_a`,`color_b`,`mortar`.
3. FIXED: a missing required finish key used to crash inside Blender (`KeyError: 'grain'`, exit 1). `rbxasset/spec.py` now validates `REQUIRED_FINISH_KEYS` per finish type and exits 2 with `finish 'oak' (type wood) is missing required key(s): grain`.
4. Hard limits seen in code: finish types wood/paint/metal/stone only (no glass, fabric, foliage, emissive); decals smear/drips/splatter; only `house` and `cabinet` builders.
5. Preview camera framing is tuned for console-sized assets.

## Generic builders batch (2026-11-22)

`match` declined all of: table, chair, bookshelf, street lamp, picket fence, wooden crate, barrel, staircase, bed, tree. Eight became builders (`table`, `chair`, `shelf`, `lamppost`, `fence`, `crate`, `barrel`, `stairs`), each run through `/test` with one shared everyday style (`blueprint/out_<name>/`). All eight built first time and read as their asset in the wide preview.

| Builder | How it looked | Known weak points |
|---|---|---|
| table | clear table: top, square legs, apron, stretchers | plain; no drawers, no tapered legs |
| chair | armchair with slatted back | slats are chunky; no seat cushion or curved back |
| shelf | five shelves with painted back | no shelf-edge detail |
| lamppost | slim post, arm and lantern, glass tint on the lens | thin in the wide shot; lens is an opaque tint, not glass |
| fence | white picket fence, capped posts | flat style only looks like it; pointed pickets untested visually |
| crate | slatted crate with lid | boards are plain boxes (no nails or grain direction) |
| barrel | belly profile, three iron hoops, lid | staves are not individual; wood grain runs the wrong way |
| stairs | six steps with solid sides and handrails | concrete uses the stone cell pattern at a large scale |

Not done (still declined): bed, tree (needs foliage and transparency).

## House variety batch (2026-11-22)

Research (roof-form guides, Pennsylvania SHPO house types, Philadelphia and DC rowhouse manuals) gave the archetypes: detached houses with gable, hip, gambrel or saltbox roofs; narrow rowhouses and brownstones (14-18 ft wide, raised basement, stoop, cornice); log cabins; barns (gambrel, big doors on the gable end); apartment blocks. The existing `house` builder is Japanese in form, so it now claims only Japanese terms and a plain "house" goes to the new `detached_house`.

New builders: `detached_house`, `rowhouse`, `apartment`, `cabin`, `barn`, sharing `facade.py` (walls with openings) and `roofs.py` (four roof forms). Matcher gained shadowing: a longer phrase from one builder beats a shorter phrase it contains from another ("japanese farmhouse" over "farmhouse").

`/test` runs (blueprint/out_house_gable, house_hip, house_gambrel, house_saltbox, rowhouse, apartment, cabin, barn; one shared buildings style): all built and read as their type.

Weak points: brick is the stone finish, so walls show large cobble-like cells instead of brick coursing (a finish limitation); roofs are plain slabs with no shingle rows; windows are simple frames; the apartment is a box; the saltbox asymmetry is subtle from the wide view; porches are minimal.

## Three realism levels (2026-11-22)

`house_gable_r1..r3` (painted walls, tiled) and `cabin_r1..r3` (wood logs, untiled). Same spec and shape; only STYLE.md changes. L1 = type + one colour, no wear; L2 = roughness, light mottle, bump, edge colour, wear edge .3 / grime .35; L3 = mottle with mottle colour, cracks, orange peel, edge chips, wear edge .55 / grime .6 / dust / water stains / streaks.

- L1 to L2: small gain (a touch of surface response, softer edges).
- L2 to L3: the clear jump, but mostly from the finish recipe (mottle + cracks turn clapboard into blotchy plaster/stucco; shingle and door get visible variation). The wear layers (grime, dust, streaks, edge chips) barely show.
- Why: tiled meshes (walls, roof, foundation) skip every position-based wear layer in the tile bake (grime, edge, moss, dust, rust crevice are skipped by design, see `finishes.py`), so for tiled parts only the noise in the recipe can add realism. Untiled wood (the cabin logs) does get wear, but it was subtle at preview distance.
- Painted siding has no board lines in the tile, so mottle plus cracks reads as stucco. Realistic clapboard needs a siding-line option in the paint recipe (not available).
- Cheapest ways to a higher level: an optional `tile_grime` for tiled finishes (a low constant plus noise, like `tile_moss`), a siding/brick line pattern, and roof shingle rows.

## Realistic buildings batch (2026-11-22)

Complaint: the earlier house variants were not realistic, nowhere near the Flatiron spike. Reading the Flatiron spike: its realism comes from dense architectural geometry (rustication, hooded windows, cornice, oriels, storefronts, awnings, AC units), soot and colour-variant meshes chosen by geometry (tiles carry no position cues), and street context. None of that existed in the pipeline builders.

What changed:
1. New finishes: `brick` (coursed, per-brick tone, whole courses per tile so it repeats) and `siding` (clapboard lines), plus `tile_grime` for tiled finishes. Brick and clapboard now read as brick and clapboard (the earlier "brick" was cobbles).
2. `rbxasset/builders/arch.py`: Face-based architectural library (walls split into colour-variant panels; plain/hooded/pedimented/surround/arched/gothic windows with sills, jambs, keystones and soot strips; doors with transoms; storefronts; cornices with brackets and dentils; string courses; quoins; rustication; balconies; oriels; porticos; columns; awnings; turrets; mansard frustums; half-timbering; fire escapes; street context).
3. Ten builders: `brownstone`, `victorian`, `tudor`, `craftsman`, `colonial_revival`, `art_deco_tower`, `haussmann`, `warehouse`, `church`, `shopfront_block`. All built with a shared `blueprint/styles/city.style.md` and viewed.

Pipeline bug found and fixed: every part is tagged with a "grain" axis along its longest side (meant for wood), and tiled UVs applied it to every finish, so tall wall panels (church, tower piers) got brick courses rotated 90 degrees. Grain now applies only to wood finishes.

Weak points (honest): windows are boxes with sash bars (no real depth reveal beyond the inset glass); glass is an opaque dark tint, not transparent; there are no interiors; dormers, turret windows and the church spire are simple; the art deco tower reads as a plain setback office tower (no relief carving); no trees, lamps or street furniture (Flatiron had them); heavy buildings are slow to build (warehouse about 4 minutes) because every box is a Blender operator call; the realism levels finding earlier still holds for wear on tiled parts, but `tile_grime` and coursed brick now carry most of it.
