---
name: test
description: Try an asset in a throwaway style without touching any game. Use when the creator types /test <asset> <style>.
---

# /test <asset> <style>

The test lane lives in `blueprint/`. Output is `blueprint/out_<asset>/` (gitignored). Ref: `blueprint/<asset>`.

Human mode (the only mode for now):
1. The creator fills `blueprint/out_<asset>/STYLE.md` themselves (same ```json style block as a game STYLE.md) and a `spec.json` next to it, or asks you to draft the spec from their words.
2. Build: `mkdir -p .superpowers && lockf .superpowers/blender.lock .venv/bin/python -m rbxasset build blueprint/<asset>`.
3. Show previews. Nothing is written into any `games/` folder.

Promoting a good test to a game: copy the spec into `games/<game>/<asset>/` and run `/make <game> <asset>` again. Do not move test output.

Agent mode (requests read from `REQUESTS.md`) is deferred.
