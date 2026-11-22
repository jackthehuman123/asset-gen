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
