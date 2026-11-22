# 03: STYLE.md

[Decided] Name: **STYLE.md**, not "style bible."

STYLE.md has two readers. The creator reads and edits it. The agent uses it at different
steps and loads only the part each step needs, which keeps token use low.

## Layering [Decided: not one file for the whole game]
Variety makes a game good, so a single style file for the whole game is out.

[Proposal] layout:
```
STYLE.md                    ← game-wide: what makes it *one* game
areas/
  village/STYLE.md          ← own shapes, materials, wear
  shrine/STYLE.md           ← can differ sharply from the village
  forest/STYLE.md
```
- **Game-wide rules hold everywhere:** scale, overall color family, overall mood, budgets.
  These keep the world feeling like one place.
- **Area rules can override the rest:** shape language, materials, wear level, accent colors.
  This is where variety between areas comes from.
- The agent loads **game STYLE.md + one area STYLE.md** per job, never all of them.

## Variety inside an area [Proposal]
- **Ranges instead of single values** where it makes sense (wear 3–5, roof sag slight to heavy,
  1–3 accent colors). The agent picks within the range.
- **Named variants** ("fisherman's hut", "headman's house", "burned house") share the area's
  look but differ in purpose and detail.

## Sections [Proposal]

| Section | What it holds | Used by |
|---|---|---|
| Intent | The creator's own words, verbatim. The anchor; it outranks everything | Judging, tiebreaks |
| Palette | 5–8 colors with roles (base, accent, grime) + colors to avoid | Surface pass, cheap color check |
| Materials | Each surface type → Roblox material/texture + condition | Surface pass |
| Wear | Decay level and *where* it shows | Prompts, surface pass |
| Shape language | Architecture, era, silhouette rules, what to avoid | Prompts, judging |
| Scale & budgets | Studs per door/wall, player height, triangle/texture limits | Cheap checks, assembly |
| Prompt kit | Short compiled style suffix + avoid list (~40 words) | Every generation call |
| References | Chosen **and rejected** samples, each with a one-line reason | Judging only |

- Rejections are recorded because "too clean," "too Western," and "reads as cute" often
  define a vibe better than the picks do.
- The prompt kit is **compiled once** from the other sections, so each generation call
  carries ~40 words of style instead of the whole file.

## Format [Proposal]
Plain markdown for people, with a small structured block at the top holding the exact values
(colors, scale, ranges) for the automatic checks.

Example values for the village area (illustrative only):
```yaml
intent: "Abandoned village where the main events happen. Horror. ..."
palette:
  base:   ["#3b3a33", "#5a4e3c"]   # soot, aged cedar
  accent: ["#7a1f1a"]              # faded shrine red, used sparingly
  avoid:  ["saturated", "pure white"]
materials:
  wood:  { roblox: WoodPlanks, condition: "wet, warped, splintered" }
  paper: { roblox: Fabric, condition: "torn, yellowed" }
wear: { level: "3-5", where: ["moss at base", "rot at joints", "water stains"] }
shape: { do: ["sagging rooflines", "nothing perfectly straight"], dont: ["modern trim"] }
scale: { door_studs: 7.5, wall_height_studs: 10, tri_budget_per_part: 4000 }
variants: ["fisherman's hut", "headman's house", "burned house"]
prompt_kit: { suffix: "...", avoid: "..." }
references: { chosen: [...], rejected: [{ id: ..., why: "too clean" }] }
```
