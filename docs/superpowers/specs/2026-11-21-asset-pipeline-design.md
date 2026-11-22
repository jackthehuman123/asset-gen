# Roblox Asset Pipeline: Design

Date: 2026-11-21 · Status: draft for approval
Background: `blueprint/` (conversation notes, open problems, research and spike log in `blueprint/05-roblox-generation.md`, spike code in `blueprint/spike/blender/`).

Labels: **[Creator]** = decided by the creator. **[Call]** = a call made during design; the creator can override it.

---

## 1. Intent

Roblox developers who have a real idea and want to go deep on it need game-ready scenery and assets that all
look like they belong to **one world**. Existing generation tools produce assets that are individually fine but
generic, blobby, inconsistent with each other, and low-fidelity ("slop"). **[Creator]**

The pipeline turns a creator's description of what they want into **themed, high-fidelity, game-ready Roblox
assets** that stay consistent across a whole game. Its core values beyond generation are **consistency** and
**token efficiency**. **[Creator]**

First real user: the creator's own horror game, set in an abandoned Japanese village (a murder took place in one
house five years ago). The pipeline is built to serve that game first, then generalized. **[Creator]**

### What the spikes established
- Roblox's own generator (`GenerationService:GenerateModelAsync`) produced rounded, blobby, inaccurate meshes,
  windows as solid blocks, and painted textures that "look like bad drawings". It isn't good enough for buildings or
  detailed furniture.
- **Quality comes first; any tool is fair game.** Roblox's generator is a means, not a requirement. **[Creator]**
- What worked ("astonishingly good" **[Creator]**): an **AI designer writes a compact style spec** from the brief,
  and **scripted, headless Blender executes it**. It builds exact geometry, applies procedural finishes and wear,
  bakes PBR maps, and exports FBX. Proven on a modern cabinet, the same cabinet restyled for the horror game, and
  an abandoned Japanese house exterior (14 meshes, 19.1k tris, about 2.5 min per build on a Mac GPU).
- **Styling is an inference task.** The AI designs how a piece should look; Blender renders it deterministically. **[Creator]**

## 2. Goals, non-goals, anti-goals

**Goals**
1. From a brief, produce an asset that matches it and fits the game's style, ready to drop into a Studio place.
2. Consistency across assets and across sessions: asset 40 matches asset 1.
3. Token efficiency: AI is used where judgment matters (design) and never to execute or render.
4. The creator stays in control and approves before anything costly or final happens. **[Creator]**
5. Minimum useful session: at least one finished, in-theme building (or set) delivered to Studio. **[Creator]**

**v1 scope** **[Creator]**: harden what the spikes proved (**house exteriors and furniture**, with the cabinet as the
reference) end to end, from brief to automatic delivery into Studio. Writing builders for new asset types is **not**
part of v1.

**Non-goals (v1)** **[Call]**
- A Studio plugin UI or a hosted web service. Interface approach A was chosen; B (a Studio plugin) is the likely next step.
- **Building interiors** and **interactive parts** (opening doors or shutters). v1 buildings are exterior shells,
  so parts can be merged by finish. Interiors can be added later, and furniture is its own asset. **[Creator]**
- New asset types beyond houses and furniture-like pieces (no new-builder authoring in v1). **[Creator]**
- Characters, rigged or animated meshes, terrain.
- Organic props via Roblox's generator or other AI 3D models (trees, statues, debris). Possible later.
- Composing whole rooms or villages (placing many assets in a scene). v1 makes assets; the creator places them.
- Deciding the game's theme or story. That's the creator's job. **[Creator]**

**Anti-goals** (failure even if it technically works)
- Generic output that looks like every other AI-generated Roblox asset.
- The pipeline inventing the theme instead of holding the creator's theme steady. **[Creator]**
- Assets that look great in Blender previews but fall apart in Studio (wrong scale, missing maps, blurry, over the triangle limit).
- Token cost that grows with every asset or session (e.g. re-sending reference boards and long style files on every call).

## 3. Constraints
- **Roblox limits:** 20,000 triangles per MeshPart. One material/SurfaceAppearance per MeshPart. Texture maps up to
  1024×1024. SurfaceAppearance maps: Color, Normal (OpenGL / tangent space), Roughness, Metalness.
- **Units:** 1 Blender unit = 1 stud. A character is about 5.5 studs tall (about 0.32 m per stud).
- **Tools on the creator's machine:** Blender 5.3 (headless, `blender -b`) is installed. The Mac GPU (Metal) works for
  Cycles baking. The first GPU run pays about 6 min of one-time setup.
- **Getting into Roblox:** Studio's 3D Importer (manual), and Open Cloud's asset upload API (needs an API key and a
  creator/group ID from the creator). Roblox's Studio MCP server may let an agent run Luau in Studio (unverified).
  One forum report says some upload paths decimate meshes (unverified).
- **Camera:** the creator's game is **first-person** (players 1–2 studs from walls); other games may be third-person.
  Close-range texel density matters. **[Creator]**
- **Blood/gore:** like a decal, not graphic. **[Creator]**
- **No Rojo required.** **[Call]** Rojo syncs scripts and files from disk into Studio. It's useful for code, but
  asset delivery doesn't depend on it.
- **AI:** the agent is the designer. Approach A runs inside an AI coding agent (Claude Code) in the creator's terminal.

## 4. Approaches considered
| | Approach | Trade-off |
|---|---|---|
| **A** ✅ | **Agent in the terminal.** The agent writes specs, runs Blender, shows previews, uploads on approval | Cheapest; reuses the spikes; core reusable by any future UI. Creators need Blender and an agent; previews are images, not in Studio |
| B | Studio plugin with a local service | Best UX for Roblox devs, previews in real game lighting. Much more to build |
| C | Hosted web service | Easiest to share with other creators; most work plus running costs; premature |

**Picked: A** **[Creator]**, built so the core (builders, finish library, spec format, upload) is separate from the
interface and B can be added without rework **[Call]**.

## 5. Design

### 5.1 The flow (one session)
```
1. Describe   creator brief (+ optional reference images; the brief outweighs them)       [Creator]
2. Sample     a few cheap variations (different specs on one builder) → pick / reject       [Creator]
3. Lock       picks and rejections update the area STYLE.md                                 [Creator]
4. Build      designer writes the asset spec → Blender builds + bakes → previews
              → creator approves, or rejects with a reason → revise
5. Deliver    upload to Roblox → asset appears in Studio, ready to drop in;
              spec + outputs + Roblox IDs saved for reuse
```
Approval is frequent and early, because a big asset with one wrong piece costs more than one wrong piece caught
early. Only the creator knows what the game should feel like. **[Creator]**
In the Blender world, "approving each part" becomes **[Call]**: the creator approves a **look** (Sample), then each
**asset** from previews. Previews include close-ups of key elements (openings, roof, hardware), and a rejection can
name one element ("tiles look like logs"). The agent revises only that element. There's no AI image judging by
default. **[Call, from earlier discussion]**

### 5.2 Core parts
| Part | What it is | Notes |
|---|---|---|
| **STYLE.md** (game + per area) | The creator-owned style file: intent in their own words, palette, **named finishes**, wear level and placement, shape rules, scale, budgets, chosen and rejected references | Layered: the game file holds what makes it one world; area files (village, shrine, forest) can override shape, materials and wear for variety. **[Creator]** Ranges and named variants give variety within an area. The agent proposes edits; the creator accepts them. **[Call]** |
| **Finish library** | Named, reusable finish recipes (wood, paint, metal, stone, …) plus wear layers (edge wear, grime, dust, moss, rain streaks, water stains, rust) | Generalized from `lib_pipeline.make_finish`. Area STYLE.md files define their named finishes (e.g. `yakisugi`, `aged_plaster`, `kawara`), and every asset in the area references them **by name**. That reuse is how consistency happens |
| **Builders** | One Python module per asset type (cabinet, house, …) that turns spec parameters into tagged parts | Deterministic, given the spec and a seed. New asset types need a new builder: the agent writes it once, the creator reviews its previews, and then it's reused cheaply. Each builder documents its parameters (its vocabulary) |
| **Asset spec** (JSON) | Written by the designer per asset: brief, design notes, dimensions and layout parameters, damage, part → finish mapping, finish overrides, wear | About 30–100 lines. Only the spec changes between variants and restyles |
| **Story decals** | Blood and similar story marks are **separate Decal assets** placed on surfaces, not baked into the asset's maps. They're non-graphic, can be removed or swapped, and are moderated separately, so a rejection never blocks the asset itself **[Creator: decal-like, not graphic; Call: separate decals]** | The designer chooses placement and look in the spec; the executor renders the decal image (with transparency) |
| **Executor** | Shared pipeline: join parts per tag → UV → bake (color/roughness/normal, plus metalness for metals) → swap to baked maps → export FBX → render previews from **baked** maps | From `lib_pipeline.py`. Guards: >20k tris per mesh is an error; texture size per mesh by area (1024 big, 512 small) |
| **Delivery** | Upload meshes and textures to Roblox; assemble the model with SurfaceAppearances in Studio | See 5.4 |
| **Asset store** | `assets/<area>/<asset>/`: spec.json, build outputs, previews, `roblox.json` (uploaded asset IDs) | Lets the next session match and reuse; specs can be rebuilt |

### 5.3 Token efficiency **[Call]**
- AI is used only to **design** (write and revise specs, update STYLE.md, write a builder once per new asset type).
  Building, baking, rendering and uploading are scripts, with zero tokens.
- Per asset the designer loads: the game STYLE.md + one area STYLE.md + the builder's parameter vocabulary. Never
  all areas, never full reference boards.
- Revisions edit the existing spec (a small diff), not rewrite it.
- Rejection reasons are compacted into the area STYLE.md's avoid list, and compacted again when it grows (open problem #5).

### 5.4 Delivery to Studio
- At house scale (14 meshes, about 45 maps) manual SurfaceAppearance linking isn't workable, so delivery must be automated.
- **Open Cloud** is Roblox's official web API for doing things outside Studio with an API key. Here it's used to
  upload meshes and images as assets owned by the creator. The creator creates the key once on the Creator
  Dashboard with asset read/write permission.
- **Owner is a setting** **[Call]**: the user or group that owns the game, so uploaded assets load in that experience.
  Set once per game in the pipeline config, alongside the API key (kept out of any files that get shared or committed).
- **[Call] Intended path:** upload mesh and texture assets via Open Cloud → get IDs → assemble a Model in Studio
  (MeshParts + SurfaceAppearances with those IDs), saved to the place or as a package.
- How the assembly runs in Studio (the Studio MCP server, a generated command-bar script, or a minimal helper
  plugin) is left to the builder, **after a verification spike** (see 7).
- Preview lighting: previews render under a lighting preset that can come from the game STYLE.md, so the creator judges
  assets in roughly game lighting (open problem #3). Final judgment happens in Studio.

### 5.4b Texel density for close-range (first-person) play **[Call]**
- Unique baked maps at 1024² are fine for detailed pieces (furniture, lattice, doors, trim) but soft on large
  surfaces seen from 1–2 studs (a 28-stud facade).
- So large flat surfaces (wall boards, plaster, roof base, floors, foundation) use **tiling textures**: each named
  finish is baked once as a seamless tile, and those meshes get UVs at a fixed studs-per-tile scale, so the texture
  repeats crisply. Position-dependent wear on them (moss at the base, rain streaks under beams) is carried by
  geometry, a small set of tile variants, or overlay decals. Unique bakes stay for detailed pieces.
- This also cuts texture memory: a village shares one set of tiles per finish instead of unique maps per house.
- The camera distance (first- vs third-person) is a game STYLE.md setting that sets the texel target.

### 5.5 Quality bar (what "done" means for an asset)
- Matches the brief and the area STYLE.md. Approved by the creator from previews.
- In Studio: correct scale next to a 5.5-stud character, every MeshPart has all its maps, ≤20k tris per mesh,
  pivot on the ground, sensible collision, no visible blur at normal play distance.

## 6. What's decided vs left to the builder
**Decided:** v1 scope = house exteriors + furniture, end to end, no interiors/interactive parts, no new builders;
first-person close range; blood as non-graphic decal-like marks; approach A; Blender + AI-written spec as the generation method; STYLE.md layering; frequent creator
approval; the creator's words outweigh references; styling done by the AI; the finish library + named finishes;
per-asset baked PBR maps; automated delivery.

**Left to the builder:** spec JSON schema details; code layout; how the agent is instructed (skill / CLAUDE.md /
commands); the Studio assembly mechanism (after the spike); bake speed tuning; preview camera choices; seed handling.

## 7. Known risks and open items
1. **Studio import/upload is unverified.** It also isn't yet known how assets get assembled in Studio from uploaded IDs. Does Open Cloud preserve triangle count and accept FBX + PNGs? Do
   imported units come out as studs? Can SurfaceAppearance maps be set from the chosen mechanism? **Verify first.**
2. **Seamless tiles from procedural finishes** are new (5.4b). Making the bake tile without visible seams, and
   keeping wear from looking repetitive, needs proving.
3. **Builder authoring** for new asset types is out of v1 scope and unproven. It's the first thing to tackle after v1.
4. **Known visual issues from spikes:** kawara reads as logs (needs round + pan tile rows); plaster too clean;
   dust reads as mold. Blood moves to separate non-graphic decals (5.2).
5. Open problems #2 (assembly from separate parts), #4 (approval fatigue), and #5 (STYLE.md growth) in
   `blueprint/04-open-problems.md` carry over.
