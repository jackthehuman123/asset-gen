# Village area style

Abandoned rural Japanese village. Charred cedar below, stained plaster above, blue-grey kawara, moss and rain streaks. One house holds the murder; the rest just feel left behind.

```json style
{
  "intent": "Abandoned Japanese village; the houses were lived in, then left five years ago after a murder.",
  "finishes": {
    "yakisugi": {
      "type": "wood",
      "base": "#2B2622",
      "grain": "#0F0D0C",
      "grain_scale": 1.4,
      "grain_contrast": 0.9,
      "roughness": 0.85,
      "bump": 0.25,
      "edge_color": "#5C4A3A"
    },
    "weathered_cedar": {
      "type": "wood",
      "base": "#6E6253",
      "grain": "#3A3129",
      "grain_scale": 1.0,
      "grain_contrast": 0.8,
      "roughness": 0.8,
      "bump": 0.2,
      "edge_color": "#958673"
    },
    "fresher_planks": {
      "type": "wood",
      "base": "#8A7257",
      "grain": "#5A4632",
      "grain_scale": 1.0,
      "grain_contrast": 0.7,
      "roughness": 0.7,
      "bump": 0.15,
      "edge_color": "#A68B6B",
      "skip_wear": [
        "moss",
        "streaks"
      ]
    },
    "roof_boards": {
      "type": "wood",
      "base": "#3A3129",
      "grain": "#1C1713",
      "grain_scale": 1.0,
      "grain_contrast": 0.7,
      "roughness": 0.85,
      "bump": 0.15
    },
    "aged_plaster": {
      "type": "paint",
      "color": "#C9C0AE",
      "roughness": 0.92,
      "orange_peel": 0.08,
      "mottle": 0.28,
      "cracks": 0.3,
      "skip_wear": [
        "moss"
      ]
    },
    "kawara": {
      "type": "paint",
      "color": "#454C53",
      "roughness": 0.5,
      "orange_peel": 0.03,
      "skip_wear": [
        "streaks"
      ]
    },
    "stone": {
      "type": "stone",
      "color_a": "#6F6B63",
      "color_b": "#4E4B45",
      "mortar": "#2E2C28",
      "cell_scale": 0.9,
      "roughness": 0.85,
      "bump": 0.4
    },
    "stained_zelkova": {
      "type": "wood",
      "base": "#5A3220",
      "grain": "#2A140B",
      "grain_scale": 1.2,
      "grain_contrast": 0.8,
      "roughness": 0.5,
      "bump": 0.15,
      "edge_color": "#8A5E3C"
    },
    "stained_zelkova_fronts": {
      "type": "wood",
      "base": "#643822",
      "grain": "#2E160B",
      "grain_scale": 1.0,
      "grain_contrast": 0.8,
      "roughness": 0.5,
      "bump": 0.15,
      "edge_color": "#8F6240"
    },
    "forged_iron": {
      "type": "metal",
      "color": "#26231F",
      "roughness": 0.65,
      "brushed": 0.1,
      "rust": 0.5,
      "rust_color": "#5C2C14",
      "edge_color": "#5A5650"
    }
  },
  "wear": {
    "edge": 0.6,
    "grime": 0.7,
    "moss": {
      "amount": 0.7,
      "color": "#3B4526"
    },
    "streaks": {
      "amount": 0.7,
      "color": "#3A3329"
    }
  },
  "avoid": [
    "too clean",
    "saturated colors",
    "modern trim"
  ]
}
```
