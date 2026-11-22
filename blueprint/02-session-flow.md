# 02: A Working Session

Example: horror game, abandoned village.

**Success for one session** [Decided]: at least one village building (or a set of buildings)
that fits the game's theme and is ready to drop into a test place in Roblox Studio, or to be
stored somewhere.

```
1. Describe    Creator's description (weighted most heavily)
               + optional reference images the creator picks
               + optional references the pipeline finds itself
                        │
2. Sample      A handful of cheap sample parts in a few directions
               → creator picks / rejects. A bad direction dies here, cheaply.
                        │
3. Lock        Picks become the area's STYLE.md (see 03)
                        │
4. Build       For each part: generate → pre-filter → creator approves → surface pass
               Then assemble → creator approves the whole
                        │
5. Deliver     Drop-in ready building + saved for reuse
```

## Step 1: Describe
- [Decided] The pipeline can use images the creator selects, or search for references on its own.
- [Decided] **The creator's own description is the most heavily weighted input.**
- [Proposal] References the pipeline finds on its own only feed STYLE.md as mood notes, and
  they are always shown to the creator before they count.

## Step 2: Sample
- [Decided] Generating a handful of samples is good. It lets the creator make a judgment
  *before* wasting tokens down a bad path.

## Step 3: Lock
See [03-style-md.md](03-style-md.md).

## Step 4: Build [Decided: approve more]
The creator approves **each part**, not only the finished building.
Reason: a big asset with one wrong piece costs more than one wrong piece caught early,
and only the creator knows what the game should feel like.

```
For each part (door, wall panel, roof, porch, …):
  1. Generate 2–4 candidates     prompt = part + area STYLE.md prompt kit
  2. Automatic pre-filter        palette check, scale/bounds check, triangle budget
  3. Creator picks one or        (a one-line reason when rejecting)
     rejects all
  4. Surface pass on the pick    materials + wear from STYLE.md
Then: assemble → creator approves the whole → deliver
```

[Proposal] details:
- **No AI vision judging by default.** The creator is the judge, so the agent only runs cheap
  numeric checks. This is the largest token saving in the pipeline. Vision checks could be
  an optional switch later.
- **2–4 candidates per part,** so one round usually produces a pick.
- **Rejections feed back** into the area STYLE.md's avoid list, so later generations learn
  (but see open problem #5).
- **Approved parts join the area's kit** and can be reused by later buildings, which saves
  generations and approvals.

## Step 5: Deliver [Proposal]
- "Drop-in ready" means one grouped model with sensible scale, a pivot on the ground, and
  collision set.
- The building is saved **together with its STYLE.md**, so the next session's building
  matches it.
