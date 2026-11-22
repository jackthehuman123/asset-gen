# Flatiron District area style

Madison Square, where Broadway crosses Fifth Avenue. Pale Indiana limestone and buff glazed terracotta facades from around 1900, black cast iron, and modern aluminium-and-glass storefronts with dark canvas awnings at street level. Grey concrete sidewalks with granite curbs, street trees in iron-edged pits, green-painted subway railings.

The city is maintained, not abandoned, but a century of traffic and rain shows:
- soot builds up under every ledge, sill, string course and cornice;
- rain streaks run down from sills;
- the stone darkens near street level.

Stone and terracotta vary a little in colour from block to block, with fine pitting. The concrete is stained and gum-spotted. No moss, no heavy decay.

How this maps to the pipeline:
- Block-to-block variation comes from geometry choosing between the `_b` variants.
- Soot under ledges comes from geometry putting the recessed faces below every projection on the `_soot` finishes.
- Street-level darkening uses `limestone_street`.
- Fine pitting comes from the small-cell stone and orange-peel bump.

```json style
{
  "intent": "Flatiron District, Manhattan, today: Beaux-Arts limestone and terracotta towers over busy modern storefronts; clean but sooty, never ruined; photoreal, not stylized.",
  "palette": {
    "limestone": "#C4BAA4",
    "terracotta_buff": "#CDBFA2",
    "soot": "#2C2924",
    "cast_iron": "#1E1F21",
    "glass": "#0E141B",
    "aluminum": "#9EA2A6",
    "awning": "#24282C",
    "concrete": "#8E8B85",
    "asphalt": "#3A3A3C",
    "street_green": "#2C3A31"
  },
  "finishes": {
    "indiana_limestone": {
      "type": "stone",
      "color_a": "#C6BCA6",
      "color_b": "#B4A991",
      "mortar": "#B0A58D",
      "cell_scale": 3.0,
      "roughness": 0.84,
      "bump": 0.12,
      "edge_color": "#DAD1BD"
    },
    "limestone_b": {
      "type": "stone",
      "color_a": "#CBBDA0",
      "color_b": "#B9AA8D",
      "mortar": "#B4A58A",
      "cell_scale": 3.4,
      "roughness": 0.86,
      "bump": 0.12,
      "edge_color": "#DDD2BA"
    },
    "limestone_street": {
      "type": "stone",
      "color_a": "#A89E89",
      "color_b": "#958B77",
      "mortar": "#8F8574",
      "cell_scale": 3.0,
      "roughness": 0.88,
      "bump": 0.14,
      "edge_color": "#BDB39E"
    },
    "limestone_soot": {
      "type": "stone",
      "color_a": "#6A645A",
      "color_b": "#56514A",
      "mortar": "#524D46",
      "cell_scale": 3.0,
      "roughness": 0.9,
      "bump": 0.12
    },
    "glazed_terracotta": {
      "type": "paint",
      "color": "#CDBFA2",
      "roughness": 0.5,
      "orange_peel": 0.15,
      "mottle": 0.35,
      "edge_color": "#E0D6C2"
    },
    "terracotta_b": {
      "type": "paint",
      "color": "#C5B596",
      "roughness": 0.52,
      "orange_peel": 0.15,
      "mottle": 0.4,
      "edge_color": "#DCD0B8"
    },
    "terracotta_soot": {
      "type": "paint",
      "color": "#8C8270",
      "roughness": 0.75,
      "orange_peel": 0.12,
      "mottle": 0.65,
      "mottle_color": "#463F36"
    },
    "cast_iron_black": {
      "type": "metal",
      "color": "#1E1F21",
      "roughness": 0.5,
      "brushed": 0.6,
      "edge_color": "#4A4B4D",
      "skip_wear": ["water_stains"]
    },
    "storefront_glass": {
      "type": "paint",
      "color": "#0E141B",
      "roughness": 0.03,
      "orange_peel": 0.0,
      "skip_wear": ["streaks", "water_stains", "edge"]
    },
    "window_sash": {
      "type": "paint",
      "color": "#2B2724",
      "roughness": 0.55,
      "orange_peel": 0.05,
      "mottle": 0.3
    },
    "aluminum_mullion": {
      "type": "metal",
      "color": "#9EA2A6",
      "roughness": 0.32,
      "brushed": 0.7,
      "skip_wear": ["streaks"]
    },
    "awning_canvas": {
      "type": "paint",
      "color": "#24282C",
      "roughness": 0.92,
      "orange_peel": 0.08,
      "mottle": 0.3,
      "skip_wear": ["edge"]
    },
    "ac_housing": {
      "type": "paint",
      "color": "#BDB9AE",
      "roughness": 0.6,
      "orange_peel": 0.05,
      "mottle": 0.35,
      "edge_color": "#8C887E"
    },
    "sidewalk_concrete": {
      "type": "stone",
      "color_a": "#95928C",
      "color_b": "#84817B",
      "mortar": "#7F7C76",
      "cell_scale": 1.6,
      "roughness": 0.9,
      "bump": 0.08,
      "skip_wear": ["streaks"]
    },
    "curb_granite": {
      "type": "stone",
      "color_a": "#77756F",
      "color_b": "#62605B",
      "mortar": "#5C5A56",
      "cell_scale": 5.0,
      "roughness": 0.7,
      "bump": 0.12,
      "skip_wear": ["streaks"]
    },
    "gum_spots": {
      "type": "paint",
      "color": "#45423E",
      "roughness": 0.6,
      "orange_peel": 0.1,
      "mottle": 0.4,
      "skip_wear": ["streaks", "water_stains"]
    },
    "street_iron_green": {
      "type": "metal",
      "color": "#2C3A31",
      "roughness": 0.55,
      "brushed": 0.5,
      "rust": 0.15,
      "rust_color": "#4A3A2A",
      "edge_color": "#56635A"
    },
    "tree_bark": {
      "type": "wood",
      "base": "#4A4038",
      "grain": "#2A241F",
      "grain_scale": 1.6,
      "grain_contrast": 0.8,
      "roughness": 0.9,
      "bump": 0.4
    },
    "foliage": {
      "type": "paint",
      "color": "#4B5640",
      "roughness": 0.85,
      "orange_peel": 0.3,
      "mottle": 0.6,
      "mottle_color": "#323B2A",
      "skip_wear": ["streaks", "water_stains", "edge"]
    },
    "tree_pit_soil": {
      "type": "stone",
      "color_a": "#3E352C",
      "color_b": "#2E2721",
      "mortar": "#221D18",
      "cell_scale": 8.0,
      "roughness": 0.95,
      "bump": 0.5,
      "skip_wear": ["streaks"]
    }
  },
  "wear": {
    "edge": 0.35,
    "grime": 0.75,
    "water_stains": 0.35,
    "streaks": {"amount": 0.85, "color": "#2C2924"}
  },
  "avoid": [
    "abandoned or ruined",
    "moss or vegetation on facades",
    "saturated colours",
    "flat uniform colours",
    "fantasy ornament",
    "real brand names or logos",
    "readable text on signs"
  ]
}
```
