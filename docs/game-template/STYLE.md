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
    "stone_name": {"type": "stone", "color_a": "#RRGGBB", "color_b": "#RRGGBB", "mortar": "#RRGGBB"},
    "brick_name": {"type": "brick", "color_a": "#RRGGBB", "color_b": "#RRGGBB", "mortar": "#RRGGBB"},
    "siding_name": {"type": "siding", "color": "#RRGGBB"}
  },
  "wear": {"edge": 0.3, "grime": 0.3},
  "avoid": ["short plain-words rules"]
}
```

Required per finish type: wood `base`+`grain`; paint `color`; metal `color`; stone, brick `color_a`+`color_b`+`mortar`; siding `color`.
Optional (add only to change the look): brick `brick_w`/`brick_h`/`mortar_size` in studs (big values make ashlar, small ones shingles and slate), siding `board_h`, any tiled finish `tile_grime` (0-1, a patchy dirt film), and roughness, bump, grain_scale, grain_contrast, edge_color, mottle (keep under 0.1 for paint or it reads as marble), mottle_color, cracks, orange_peel, brushed, rust, rust_color, cell_scale, skip_wear.
`camera`, `lighting`, `budgets` are game-level; area files omit them and carry only finishes, wear and avoid deltas.
