---
name: test
description: Try an asset in a throwaway style without touching any game. Use when the creator types /test <asset> <style>, where <style> is free text describing the look.
---

# /test <asset> <style>

The test lane lives in `blueprint/`. Output is `blueprint/out_<asset>/` (gitignored). Ref: `blueprint/<asset>`. Nothing is ever written into a `games/` folder.

`<asset>` is a short name (it becomes the folder name, snake_case). `<style>` is the creator's own words about the look, anything from "pale oak and white, Scandinavian" to a paragraph. It is not a file name.

## Steps

0. **Match the builder.** Run `.venv/bin/python -m rbxasset match <the asset's form words>` (the asset name and any shape words the creator gave; leave the style words out, they cause false hits). It prints a confidence per builder and a verdict:
   - `build` (0.8 or higher): continue with that builder.
   - `ask` (0.5 to 0.79, or two builders within 0.1): show the creator the scores and reasons, say what the builder cannot do, and wait for their yes. You may move a score by at most 0.2 with a stated reason.
   - `decline` (below 0.5): say it is a gap, still write the STYLE.md (step 1) so the style can be judged, and stop. Propose a new builder; do not improvise a spec.
1. **Extract the style.** Read `docs/game-template/STYLE.md` and write `blueprint/out_<asset>/STYLE.md` from the creator's words:
   - Prose: three to six sentences, using their words. Never invent a theme they did not give; where you fill a gap (a colour, a roughness), say so in one line in the prose.
   - JSON block: `intent`, `lighting` preset, and only the finishes the look needs, with just the required keys per type (wood `base`+`grain`; paint and metal `color`; stone `color_a`+`color_b`+`mortar`). Add optional keys only when they change the look. Keep paint `mottle` under 0.1. Add `wear` and `avoid` when the words imply them.
   - A style describes look, never form. If the creator describes a shape, put it in the spec, not the style.
2. **Draft the spec.** `.venv/bin/python -m rbxasset new blueprint/<asset> --builder house|cabinet`, then fill `brief`, `params`, and `parts` (every part tag gets one of the finishes you just defined). Use the builder step 0 chose.
3. **Build.** `mkdir -p .superpowers && lockf .superpowers/blender.lock .venv/bin/python -m rbxasset build blueprint/<asset>`. Exit 2 means a style or spec error (fix the file); exit 1 is a build failure.
4. **Show.** Open the previews in `blueprint/out_<asset>/out/previews/` and show the creator the STYLE.md next to them. They judge how well the style carried over.

Revising: edit the existing STYLE.md or spec with a small change and rebuild.

Promoting a good test to a game: copy the spec into `games/<game>/<asset>/` and run `/make <game> <asset>` again. Do not move test output.

Agent mode (requests read from `REQUESTS.md`) is deferred.
