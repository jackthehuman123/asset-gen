# 01: Vision

## What it is
A pipeline that uses Roblox's own asset generation to create assets and refine them.
Its two core values, beyond just generating assets: **consistency** and **token efficiency**. [Decided]

## Who it's for [Decided]
Roblox developers who have an idea and want to go deep on it. It is not for the "slop" game
automation tools that already exist. Those games make money, but this tool is for a
different kind of developer.

## Why assets first [Decided]
Good scenery and assets are one of the first steps in making a good Roblox game.
A world has to feel like one place. In horror, atmosphere is most of the experience.

## First real user [Decided]
The creator's own horror game. The main events happen in an abandoned village.
Visual inspiration so far: generic scenes from games like *The Mimic*. That's mood only.
No clear picture yet of what the houses should look like.

[Proposal] Build it to work for this game first, then generalize. Horror is a good stress
test: muted palettes, grime, wear, consistent decay. Generic AI output, which tends to be
clean and saturated, drifts from all of these.

## The two problems seen so far [Decided]
1. **No vibe.** Generated houses are generic pieces that don't fall under any theme.
2. **Low fidelity.** Builds stop at blocky, crude pieces and textures. They lack real texturing
   and attention to depth, which makes a world of difference to the player experience.

[Proposal] Fidelity probably won't come from better prompts. A single generated mesh has a
limited detail budget, and a one-shot house spends it on overall shape. Fidelity in good
Roblox builds usually comes from:
- **Composition.** Generate *parts* (window frames, warped boards, trim, door, porch) and
  assemble them, so each part gets the full detail budget.
- **Real surface maps.** SurfaceAppearance with normal and roughness maps, plus grime and
  wear decals, instead of a single flat color texture.
- **Lighting and atmosphere.** Outside the asset pipeline, but it matters (see open problem #3).

So the pipeline produces **themed kits of parts**, not finished buildings in one shot.

## Scope boundary [Decided]
- Deciding the theme (writing the story, designing the world) is **a human's job**. The
  pipeline does not invent it. Most creators don't have a clear picture of the final
  product, and that's expected.
- The pipeline's job is to **hold the theme steady** once it exists, so asset 40 matches asset 1.
- [Proposal] The gap between a fuzzy idea and a concrete theme is closed by *capturing* the
  creator's decisions (see the Sample and Lock steps in 02), not by the pipeline deciding for them.

## Guardrail [Proposal]
References set the *mood*. Outputs are the creator's own. The pipeline does not reproduce
another game's actual assets.
