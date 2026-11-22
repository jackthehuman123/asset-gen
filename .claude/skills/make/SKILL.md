---
name: make
description: Build an official asset for a game with the rbxasset pipeline. Use when the creator types /make <game> <asset>, or approves a request in games/<game>/REQUESTS.md.
---

# /make <game> <asset>

Arguments: the game folder name under `games/`, and the asset name. The ref for every pipeline command is `<game>/<asset>`.

0. Match the builder: `.venv/bin/python -m rbxasset match <the request's Need line>`. `build` (0.8+) continues; `ask` (0.5-0.79 or a tie within 0.1) goes to the creator with the scores and the builder's limits before anything is built; `decline` (<0.5) is a gap: set the request to `rejected` with the reason and propose a new builder. You may move a score by at most 0.2 with a stated reason.
1. Load only: `games/<game>/STYLE.md`, `games/<game>/GAME.md` if it exists, the asset's entry in `games/<game>/REQUESTS.md`, the area style named by the spec's optional `"area"` key, and the builder's `vocab.py`. Read nothing from other games.
2. Follow the asset-pipeline skill (`.claude/skills/asset-pipeline/SKILL.md`) with ref `<game>/<asset>`: sample, lock, build, show previews.
3. Output lands in `games/<game>/<asset>/out/`. Set the request's status to `built` once the creator approves the result.
4. Failure means the creator's judgement: the asset built but is not good enough. Set the status to `rejected`, write the creator's reason in the entry's `Result` line, and propose an `avoid` line. Technical errors (exit 1 or 2) are yours to fix; do not put Blender logs into the game folder.
