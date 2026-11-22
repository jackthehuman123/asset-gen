# 04: Open Problems

Holes found in the design so far, worst first. None are resolved yet.

## 1. Part-level detail is untested
The parts approach assumes a generated *wall panel* comes out more detailed than a generated
*house*. That's a guess, not a tested fact. If Roblox's generator produces blobby, low-detail
shapes at any size, splitting a house into parts doesn't fix fidelity.
It's also unconfirmed whether image input can be scripted or only works by hand in Studio.
**Thinking won't settle this; testing will:** generate a door, a wall panel, and a whole house
with the same style suffix and compare them. → Being researched in [05](05-roblox-generation.md).

## 2. Assembly: generated parts don't fit together
Each part comes back with its own size, its own pivot, and edges that don't line up. A roof
generated on its own won't sit on walls generated on their own.
Open: who makes them fit (the agent, the creator, or a fixed template that tells each part
what size to be)? Does the layout of the house come first, or the parts?

## 3. Approval happens under different lighting than the game
Horror depends on lighting (fog, darkness, a single lantern). A part approved under Studio's
default bright light will look different in the game. If the approval view doesn't use the
game's lighting, the creator approves the wrong things.
Possible direction: put a lighting preset in the game STYLE.md and preview candidates under it.

## 4. Approval fatigue
Roughly 15 parts per house × 3 candidates × rerolls comes to 50+ looks per building.
The creator chose to approve more on purpose. At what point does that stop protecting
quality and start eating the session?

## 5. STYLE.md grows with every rejection
Every rejection adds to the avoid list. After a few sessions the area STYLE.md is long,
partly contradictory, and carried into every prompt, so the token savings fade over time.
It's also the creator's file being edited by the agent.
Possible direction: the agent proposes edits and the creator accepts them; compact the file periodically.

## 6. Retexturing may not be scriptable
The surface pass assumes the agent can retexture a generated mesh. Roblox's new texture tools
may work only by hand in Studio, and generated meshes may lack clean UV maps (the layout
that tells a texture where to sit on the mesh).

## Smaller
- **Rate limits.** Many candidates × many parts × rerolls may hit Roblox's generation quotas.
- **Export.** Can generated meshes be saved *outside* Roblox, or do they live only as Roblox assets?

## Updates from research (see 05)
- **#1** Still untested. Knobs to test: `MaxTriangles`, `Size`, `Image`, text-only vs image+text.
- **#2** New possible path: custom `SchemaDefinition` generates one model as named groups (walls, roof, door…).
- **#6** Mostly confirmed. Texturing an existing mesh is Studio UI only; no API found.
- **Export** Not stated anywhere. Still open.
