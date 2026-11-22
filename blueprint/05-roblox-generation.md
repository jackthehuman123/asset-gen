# 05: What Roblox's Generators Can Do (research, 2026-11-21)

Sources: the official GenerationService reference and model-generation guide, plus forum posts
and third-party guides. The DevForum announcement posts could not be fetched automatically
(the site returned empty pages), so anything sourced only from them is marked *unverified*.

## The scriptable API: `GenerationService`

| Method | Status | Where it runs |
|---|---|---|
| `GenerateMeshAsync` | **Deprecated.** Roblox announced a sunset; use `GenerateModelAsync` | Server scripts |
| `GenerateModelAsync(inputs, schema, options?)` | Current | Server Script (all official samples). Plugin/command bar: **not stated** |
| `LoadGeneratedMeshAsync(generationId)` | Current; loads a result once per ID | Client scripts |
| `SegmentMeshAsync(meshPart, schema, options?)` | Current | **Studio only** (edit mode or plugin) |

### `GenerateModelAsync` inputs (official)
- `TextPrompt`: string. Required unless an image is given.
- `Image`: an image asset (`Content.fromAssetId(id)`). **Image input is scriptable.**
  Format and size requirements: not stated.
- `Size`: Vector3. **Approximate** target size.
- `MaxTriangles`: integer. Lower means more low-poly.
- `GenerateTextures`: boolean, default true.
- `options`: "currently not used." There's no seed, so results can't be reproduced exactly.

### Schemas: named multi-part output (official)
- Predefined: `Car5` (body + 4 wheels) and `Body1` (single mesh). The guide says these are the only two.
- Custom `SchemaDefinition`: a `Groups` list of part names (e.g. `{"walls","roof","door","porch"}`).
  The returned Model "is organized to match the named groups."
- Exact naming and behavior rules for custom schemas: not stated.
- Returns: a Model plus a metadata table (with a UUID).

### Limits
- Rate: about **10 requests/minute per experience**, scaling with concurrent users
  (third-party source; the beta was 5/min). Not stated on the official page.
- Triangles: only the user-set `MaxTriangles`. Roblox's per-mesh cap is 20k (general mesh rule).
- Texture resolution, PBR maps (normal/roughness): **not stated.**
- Saving/publishing/exporting generated output: **not stated.**

## Studio-only tools (not scriptable)
- **Texture generation on an existing mesh**: Studio ribbon, right-click → Generate → Texture,
  or `/generate_texture` in Assistant (third-party guide, Sept 2026). No API found.
- **Segment Any Mesh**: splits an imported mesh into parts. Available in Studio and through
  `SegmentMeshAsync` (Studio context only).
- **Image → mesh in Assistant**: `/generate_mesh` has an Image mode.
- **Studio MCP server** (lets an outside agent drive Studio): reportedly includes
  `generate_mesh` and `generate_material` tools, but no texture or segment tools. *Unverified.*
- Roadmap: "Open Cloud APIs for AI tools" (Mid → Late 2026), and an improved texture tool (Late 2026).
  Neither confirmed shipped.

## Quality (weakest evidence)
- 2025 beta reports: meshes okay for simple objects, **textures poor**, complex objects limited.
  One tester: "none … of the AI generated meshes were good enough to be used."
- Bounding-box control and quality updates shipped later in 2025.
- **Current quality for our use (detailed, worn architectural parts): unknown.** Only a test will tell.

## What this means for the blueprint
- **Open problem #1 (detail):** still untested, but there are now real knobs to test:
  `MaxTriangles`, `Size`, `Image`, text-only vs image+text.
- **Open problem #2 (assembly):** custom schemas are a potential new path. Generate a house
  *as named groups* in one call, instead of separate parts that don't fit. Whether one group can be
  regenerated without the others is unknown. `Size` helps parts come out at roughly the right scale.
- **Open problem #6 (retexturing):** mostly confirmed. Texturing an existing mesh is Studio UI only.
  The automated surface pass would have to rely on `GenerateTextures`, Roblox materials or
  MaterialVariants, SurfaceAppearance images we supply, or a manual Studio step.
- **Image-to-asset:** confirmed scriptable through the `Image` input, so the project name holds.
- **Automation shape:** generation runs inside a Roblox server (or Studio play-test), not from an
  outside service, until the Open Cloud AI APIs ship. The pipeline needs something running inside
  Studio: a plugin, a play-test script, or the Studio MCP server.

## Sources
- https://create.roblox.com/docs/reference/engine/classes/GenerationService
- https://create.roblox.com/docs/parts/model-generation
- https://github.com/Roblox/creator-docs/blob/main/content/en-us/reference/engine/classes/GenerationService.yaml
- https://devforum.roblox.com/t/early-preview-generate-3d-models-segmented-into-multiple-parts/4678458
- https://devforum.roblox.com/t/beta-cube-3d-generation-tools-and-apis-for-creators/3558947
- https://devforum.roblox.com/t/beta-cube-3d-model-updates-better-quality-and-bounding-box-control/3828156
- https://bloxbot.ai/guide/roblox-ai-texture-generation-mesh-segmentation-2026
- https://devforum.roblox.com/t/creator-roadmap-2026-fall-update/4880208
- https://www.kitsblox.com/blog/roblox-ai-tools-developers-2026

## Findings from the spike
- **Run 1:** generated models came back about **2 studs tall**, roughly 2/5.5 of a character's height.
  The `Size` input did not set the output scale. The pipeline has to rescale every result itself
  (`Model:ScaleTo`), which also affects texture density. Scaling up stretches textures. Check this in run 2.
- **Run 2 (after scaling):** textures look **blurred and smeared up close**. Scaling up stretches them.
  Only the two segmented houses were judged bad, because their **windows weren't see-through**.
  The other results were not called out as bad.
- **Creator's idea [Decided to test]:** get depth from **real 3D geometry / bumps** instead of
  image-like painted textures.
- **Run 3 setup:** one house generation per run (creator's call). A segmented house with a prompt that
  asks for modeled relief, copied 2–3 times with different surfaces: generated texture vs Roblox
  materials (tiled, with built-in normal maps) vs a custom MaterialVariant. The windows group is
  set to glass in every copy.
- **Run 3 results (creator's observations):**
  - Asking for "every plank modeled as separate geometry" **did not work**. The house came back as one
    unified mesh. The planks only came from the Roblox material's texture, but that **did help fidelity**.
  - The GENERATED (painted texture) copy "looks like bad drawings."
  - **Shapes are rounded, with no sharp corners.** That's bad for architecture.
  - Windows on the MATERIALS copy are **solid glass blocks clipping through the walls**. The walls have
    no openings; the generator makes windows as solid volumes, not holes.
- **Takeaways:** Roblox materials beat generated textures. The generator is weak at
  architecture: crisp edges, flat walls, real openings, separable pieces.
- **Run 4 setup:** layout → generate each piece → assemble. A part-built shell with real openings and slots,
  5 generated piece types (window frame, shutter, door, corner post, ridge) snapped in with math.
- **Creator raised Blender** as an option (2026-11-21). See discussion; not yet decided.
- **Decision [Decided]:** anything that gets the quality is fair game. Roblox's generator is a means, not a
  requirement. Blender and other tools are allowed.
- **Run 4 results:** "not a bad start." Individual pieces look **detailed**, but **aren't exactly what they
  should be** (prompt adherence).
- **Layout direction [Decided]:** don't generate a physical layout first. Keep only the **expected location**
  of each piece. Generate the pieces, **take their dimensions**, then work out what the room/house should
  look like from them (bottom-up).
- **Run 5 setup:** a bedroom. 7 pieces generated, each scaled by one real-world reference dimension; the room
  size, wall holes and positions are computed from the measured pieces.
- **Run 6 setup:** a single detailed piece (modern cabinet) at 20k triangles, generated texture vs Roblox material.
- **Blender spike:** a modern cabinet built by a Python script in Blender 5.3 (headless). It matched the brief
  exactly on the first try (2 doors, 3 drawers, bar handles, tapered legs, sharp beveled edges, seams):
  2 meshes, about 2.7k tris total. Exported as FBX for the Studio 3D Importer. Studio import not yet verified.
- **Styling decision [Decided]:** styling is an inference task. The AI designs how the piece should look; Blender executes.
- **Styling spike:** brief "TV cabinet, modern American white living room." The AI-written spec changed the
  proportions (low and wide TV console, 2 studs tall × 5.4 wide), went two-tone (light oak frame and top,
  matte warm-white fronts), with matte black handles. Blender built it, joined parts by finish (3 meshes,
  about 2.7k tris), baked 4 PBR maps per mesh and exported FBX with embedded textures. Preview from the baked
  maps looks right. Weak spot: the oak grain is faint and blotchy on the side panels (the grain recipe
  needs work). Studio import not yet verified.
- **Restyle spike (abandoned Japanese murder house):** same geometry and pipeline; only the spec changed
  (`specs/tv_console_abandoned_japanese.json`). Added wear layers (edge wear, grime, dust, water stains, blood)
  and metal rust, plus wood grain that follows each board's long axis.
  - Works: stained-zelkova grain reads as real wood, rusted iron handles convincing, lower and Japanese
    proportions, dust on the top, worn edges.
  - Weak: the blood drips read as dark wood streaks (too dark and brown against dark stain). The dust looks
    blotchy, like mold. Water stains are barely visible.
  - Cost: the bake took about **9 minutes** on CPU (crevice and edge detection need many samples). It needs speeding up
    (GPU, 512² maps, or baking the wear masks only once).
- **House exterior spike:** `specs/house_abandoned_japanese.json` → `house.py` (shared code in `lib_pipeline.py`).
  The AI-written spec sets layout (bays per facade: wall/window/door), proportions, damage (sagging ridge, missing
  and slipped tiles, missing or broken boards, snapped lattice, missing veranda planks), one boarded window, one
  half-open door, and finishes (yakisugi, weathered cedar, aged plaster, kawara, stone) with moss, rain streaks,
  grime and edge wear.
  - Output: 1,012 pieces joined into 14 meshes, **19.1k tris total** (largest mesh is about 5.6k). Textures at 1024² for big surfaces
    and 512² for small ones. Full run **2.5 min** (bake 2 min on GPU; the first-ever GPU run adds about 6 min of one-time setup).
  - Works: reads as a Japanese minka at a glance. Real openings with depth, broken lattice, the boarded window
    reads as "after", the half-open door, the sagging ridge, the veranda and stone base.
  - Weak: kawara rows are full round tubes side by side, so they read as logs. Real kawara alternate
    round cover tiles with concave pan tiles. Plaster is a bit too clean. Moss mostly hidden under tiles.
  - Not yet verified in Studio. 14 meshes × 3–4 maps is about 45 images, so manual SurfaceAppearance linking
    would be painful. Automated upload (Open Cloud) becomes necessary at this scale.
