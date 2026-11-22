---
name: make
description: Build an official asset for a game with the rbxasset pipeline. Use when the creator types /make <game> <asset>, or approves a request in games/<game>/REQUESTS.md.
---

# /make <game> <asset>

Arguments: the game folder name under `games/`, and the asset name. The ref for every pipeline command is `<game>/<asset>`.

1. Load only: `games/<game>/STYLE.md`, `games/<game>/GAME.md` if it exists, the asset's entry in `games/<game>/REQUESTS.md`, the area style named by the spec's optional `"area"` key, and the builder's `vocab.py`. Read nothing from other games.
2. Follow the asset-pipeline skill (`.claude/skills/asset-pipeline/SKILL.md`) with ref `<game>/<asset>`: sample, lock, build, show previews.
3. Output lands in `games/<game>/<asset>/out/`. Set the request's status to `built` once the creator approves the result.
4. Failure means the creator's judgement: the asset built but is not good enough. Set the status to `rejected`, write the creator's reason in the entry's `Result` line, and propose an `avoid` line. Technical errors (exit 1 or 2) are yours to fix; do not put Blender logs into the game folder.
