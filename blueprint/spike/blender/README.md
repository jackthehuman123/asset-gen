# Spike: Blender → Studio (throwaway)

Question: **can a scripted Blender model hit the quality bar that Roblox's generator couldn't?**

## Build (already done once; rerun to regenerate)
```
blender -b --factory-startup -P cabinet.py -- "$PWD/out"
```
Outputs `out/cabinet.fbx` (import this) and `out/cabinet.png` (preview).
Result: 2 meshes (`Cabinet_Wood` 1,752 tris, `Cabinet_Metal` 980 tris).

## Into Studio
1. **File → Import 3D**, then pick `out/cabinet.fbx`. Keep it as one model; note the importer's unit/scale setting.
2. Select the imported model, then paste `ApplyMaterials.lua` into the **Command Bar** and press Enter.
   It applies Roblox Wood/Metal by mesh name, fixes the scale to 3 studs tall, and adds a 5.5-stud marker.

## Bring back
- Imported size printed in Output (tells us the unit conversion).
- Did it import as 2 MeshParts? Did the triangle count survive (no decimation)?
- Up close in Studio: sharp edges, seams, handles. Does it hold up?
- Compare with run 6 (Roblox-generated cabinet).

---

# Spike 2: AI-designed styling (style spec → Blender → baked maps)

```
blender -b --factory-startup -P cabinet_styled.py -- "$PWD/specs/tv_console_modern_white.json" "$PWD/out_styled"
```
(about 50 seconds on this Mac)

- `specs/tv_console_modern_white.json` is the **style spec**, written by the AI "designer" from the creator's brief:
  proportions, which finish goes on which part, and the finish recipes (wood / paint / metal).
- `cabinet_styled.py` builds the cabinet from it, joins parts by finish (3 meshes), bakes
  color / normal / roughness / metalness maps (1024²) per mesh, exports `out_styled/cabinet_styled.fbx`
  with embedded textures, and renders `preview_wide.png` / `preview_close.png` **from the baked maps**.

## Into Studio
1. **File → Import 3D** → `out_styled/cabinet_styled.fbx`. Check whether the importer creates SurfaceAppearances
   with all 4 maps.
2. If it only brings the color map (or none): import the 12 PNGs from `out_styled/textures/`
   (Asset Manager → Bulk Import), then on each MeshPart add a SurfaceAppearance and set
   ColorMap / NormalMap / RoughnessMap / MetalnessMap.

---

# Spike 3: House exterior
```
blender -b --factory-startup -P house.py -- "$PWD/specs/house_abandoned_japanese.json" "$PWD/out_house"
```
Outputs `out_house/house.fbx`, `out_house/textures/`, 4 previews. About 2.5 minutes on the Mac GPU.
