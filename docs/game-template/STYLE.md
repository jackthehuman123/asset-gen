# <Game or area> style  (DRAFT template)

Three to six sentences of prose: the mood, one reference, what makes this look special, what the world has been through. Prose is for the creator and for the agent's judgement; only the JSON block is parsed.

Rules: a style describes look, never form (form is the builder and the spec's params). List only the keys that change the look; the rest default.

```json style
{
  "intent": "One sentence: where, when, how it feels.",
  "camera": "first_person",
  "lighting": {"preset": "overcast_exterior"},
  "budgets": {"max_tris_per_mesh": 20000, "texture_big": 1024, "texture_small": 512},
  "finishes": {
    "wood_name":  {"type": "wood",  "base": "#RRGGBB", "grain": "#RRGGBB"},
    "paint_name": {"type": "paint", "color": "#RRGGBB"},
    "metal_name": {"type": "metal", "color": "#RRGGBB"},
    "stone_name": {"type": "stone", "color_a": "#RRGGBB", "color_b": "#RRGGBB", "mortar": "#RRGGBB"}
  },
  "wear": {"edge": 0.3, "grime": 0.3},
  "avoid": ["short plain-words rules"]
}
```

Required per finish type: wood `base`+`grain`; paint `color`; metal `color`; stone `color_a`+`color_b`+`mortar`.
Optional (add only to change the look): roughness, bump, grain_scale, grain_contrast, edge_color, mottle (keep under 0.1 for paint or it reads as marble), mottle_color, cracks, orange_peel, brushed, rust, rust_color, cell_scale, skip_wear.
`camera`, `lighting`, `budgets` are game-level; area files omit them and carry only finishes, wear and avoid deltas.
