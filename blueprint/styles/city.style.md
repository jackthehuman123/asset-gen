# Shared test style: city masonry

Reused by the realism-first building tests. Every value is my fill.

```json style
{
  "intent": "Present-day city buildings with realistic masonry: brownstone, brick, trim, iron, soot under every ledge.",
  "camera": "first_person",
  "lighting": {
    "preset": "overcast_exterior"
  },
  "finishes": {
    "brownstone_stone": {
      "type": "brick",
      "color_a": "#7C5C49",
      "color_b": "#6C4E3D",
      "mortar": "#4F3A2C",
      "brick_w": 2.4,
      "brick_h": 0.9,
      "mortar_size": 0.06,
      "tile_grime": 0.25,
      "bump": 0.3
    },
    "brownstone_b": {
      "type": "brick",
      "color_a": "#86644F",
      "color_b": "#74553F",
      "mortar": "#4F3A2C",
      "brick_w": 2.4,
      "brick_h": 0.9,
      "mortar_size": 0.06,
      "tile_grime": 0.25,
      "bump": 0.3
    },
    "brick_red": {
      "type": "brick",
      "color_a": "#8A4637",
      "color_b": "#733A2E",
      "mortar": "#A99F90",
      "tile_grime": 0.35,
      "bump": 0.45
    },
    "sandstone_trim": {
      "type": "paint",
      "color": "#9A8068",
      "roughness": 0.8,
      "mottle": 0.08,
      "orange_peel": 0.05
    },
    "sash_white": {
      "type": "paint",
      "color": "#E9E6DE",
      "roughness": 0.5
    },
    "glass_dark": {
      "type": "paint",
      "color": "#34444E",
      "roughness": 0.05
    },
    "door_paint": {
      "type": "paint",
      "color": "#2A1A18",
      "roughness": 0.4,
      "mottle": 0.05
    },
    "soot_dark": {
      "type": "paint",
      "color": "#5E4B3F",
      "roughness": 0.9,
      "mottle": 0.09,
      "tile_grime": 0.3
    },
    "iron_black": {
      "type": "metal",
      "color": "#1C1C1E",
      "roughness": 0.5,
      "rust": 0.1
    },
    "groove_dark": {
      "type": "paint",
      "color": "#3A2C24",
      "roughness": 0.9
    },
    "roof_tar": {
      "type": "paint",
      "color": "#34363A",
      "roughness": 0.9,
      "mottle": 0.08,
      "tile_grime": 0.3
    },
    "sidewalk": {
      "type": "brick",
      "color_a": "#8F8C86",
      "color_b": "#7F7C76",
      "mortar": "#4E4C48",
      "brick_w": 2.0,
      "brick_h": 2.0,
      "mortar_size": 0.07,
      "tile_grime": 0.4,
      "bump": 0.2
    },
    "curb_granite": {
      "type": "stone",
      "color_a": "#7C7F82",
      "color_b": "#6C6F72",
      "mortar": "#55585A",
      "cell_scale": 0.8
    },
    "asphalt": {
      "type": "paint",
      "color": "#2E2F31",
      "roughness": 0.95,
      "mottle": 0.09,
      "tile_grime": 0.3
    },
    "foundation_stone": {
      "type": "brick",
      "color_a": "#8A8780",
      "color_b": "#706D67",
      "mortar": "#4E4C48",
      "brick_w": 1.6,
      "brick_h": 0.8,
      "mortar_size": 0.07,
      "tile_grime": 0.4,
      "bump": 0.4
    },
    "clapboard_cream": {
      "type": "siding",
      "color": "#CDBB8C",
      "board_h": 0.5,
      "tile_grime": 0.3,
      "bump": 0.5
    },
    "clapboard_cream_b": {
      "type": "siding",
      "color": "#C2B080",
      "board_h": 0.5,
      "tile_grime": 0.3,
      "bump": 0.5
    },
    "shingle_green": {
      "type": "brick",
      "color_a": "#6E8266",
      "color_b": "#5C7058",
      "mortar": "#2C3828",
      "brick_w": 0.5,
      "brick_h": 0.4,
      "mortar_size": 0.05,
      "bump": 0.5
    },
    "trim_burgundy": {
      "type": "paint",
      "color": "#7A3E4B",
      "roughness": 0.5,
      "mottle": 0.06
    },
    "soot_light": {
      "type": "paint",
      "color": "#7A6F5C",
      "roughness": 0.9,
      "mottle": 0.09,
      "tile_grime": 0.3
    },
    "roof_shingle": {
      "type": "brick",
      "color_a": "#4C5056",
      "color_b": "#3E4248",
      "mortar": "#26282C",
      "brick_w": 0.9,
      "brick_h": 0.45,
      "mortar_size": 0.05,
      "tile_grime": 0.35,
      "bump": 0.5
    },
    "slate_roof": {
      "type": "brick",
      "color_a": "#4A5058",
      "color_b": "#3A4048",
      "mortar": "#22262A",
      "brick_w": 0.9,
      "brick_h": 0.6,
      "mortar_size": 0.05,
      "tile_grime": 0.3,
      "bump": 0.5
    },
    "plaster_cream": {
      "type": "paint",
      "color": "#D9CDB0",
      "roughness": 0.9,
      "mottle": 0.09,
      "cracks": 0.1,
      "tile_grime": 0.35
    },
    "plaster_b": {
      "type": "paint",
      "color": "#CFC2A2",
      "roughness": 0.9,
      "mottle": 0.09,
      "cracks": 0.1,
      "tile_grime": 0.35
    },
    "timber_dark": {
      "type": "wood",
      "base": "#3A281C",
      "grain": "#22160E",
      "grain_contrast": 0.6,
      "roughness": 0.8,
      "bump": 0.3
    },
    "sash_dark": {
      "type": "paint",
      "color": "#2A2420",
      "roughness": 0.5
    },
    "door_oak": {
      "type": "wood",
      "base": "#4A3220",
      "grain": "#2A1A10",
      "grain_contrast": 0.7,
      "roughness": 0.6
    },
    "siding_olive": {
      "type": "siding",
      "color": "#6E7A58",
      "board_h": 0.55,
      "tile_grime": 0.3,
      "bump": 0.5
    },
    "siding_olive_b": {
      "type": "siding",
      "color": "#66724F",
      "board_h": 0.55,
      "tile_grime": 0.3,
      "bump": 0.5
    },
    "shingle_brown": {
      "type": "brick",
      "color_a": "#6B4F36",
      "color_b": "#5A4029",
      "mortar": "#2C1E12",
      "brick_w": 0.55,
      "brick_h": 0.45,
      "mortar_size": 0.05,
      "bump": 0.5
    },
    "trim_cream": {
      "type": "paint",
      "color": "#D8CFB6",
      "roughness": 0.55,
      "mottle": 0.06
    },
    "brick_dark": {
      "type": "brick",
      "color_a": "#6E3A2E",
      "color_b": "#5A2E25",
      "mortar": "#8E877A",
      "tile_grime": 0.35,
      "bump": 0.45
    },
    "roof_brown": {
      "type": "brick",
      "color_a": "#5A4A3A",
      "color_b": "#4A3C30",
      "mortar": "#2A2018",
      "brick_w": 0.9,
      "brick_h": 0.45,
      "mortar_size": 0.05,
      "tile_grime": 0.35,
      "bump": 0.5
    },
    "brick_flemish": {
      "type": "brick",
      "color_a": "#8F4A38",
      "color_b": "#733A2E",
      "mortar": "#B5AC9C",
      "tile_grime": 0.3,
      "bump": 0.45
    },
    "brick_flemish_b": {
      "type": "brick",
      "color_a": "#A05A44",
      "color_b": "#84463A",
      "mortar": "#B5AC9C",
      "tile_grime": 0.3,
      "bump": 0.45
    },
    "door_navy": {
      "type": "paint",
      "color": "#1E2A3E",
      "roughness": 0.4
    },
    "shutter_green": {
      "type": "paint",
      "color": "#2E4A3A",
      "roughness": 0.55,
      "mottle": 0.06
    },
    "iron_black2": {
      "type": "metal",
      "color": "#1C1C1E",
      "roughness": 0.5
    },
    "trim_white": {
      "type": "paint",
      "color": "#EEEBE4",
      "roughness": 0.5,
      "mottle": 0.05
    },
    "limestone": {
      "type": "brick",
      "color_a": "#C4B89C",
      "color_b": "#B4A88C",
      "mortar": "#8E846E",
      "brick_w": 2.6,
      "brick_h": 1.0,
      "mortar_size": 0.06,
      "tile_grime": 0.3,
      "bump": 0.3
    },
    "limestone_b": {
      "type": "brick",
      "color_a": "#CBBFA3",
      "color_b": "#BCB094",
      "mortar": "#8E846E",
      "brick_w": 2.6,
      "brick_h": 1.0,
      "mortar_size": 0.06,
      "tile_grime": 0.3,
      "bump": 0.3
    },
    "limestone_trim": {
      "type": "paint",
      "color": "#CBBFA6",
      "roughness": 0.8,
      "mottle": 0.08
    },
    "bronze_dark": {
      "type": "metal",
      "color": "#3C372E",
      "roughness": 0.45,
      "brushed": 0.2
    },
    "zinc_roof": {
      "type": "brick",
      "color_a": "#666C72",
      "color_b": "#585E64",
      "mortar": "#363A3E",
      "brick_w": 1.6,
      "brick_h": 0.5,
      "mortar_size": 0.05,
      "tile_grime": 0.3,
      "bump": 0.4
    },
    "door_steel": {
      "type": "paint",
      "color": "#4A5A5C",
      "roughness": 0.5,
      "mottle": 0.06
    },
    "church_stone": {
      "type": "brick",
      "color_a": "#8E8A80",
      "color_b": "#7A766C",
      "mortar": "#55524A",
      "brick_w": 2.0,
      "brick_h": 1.0,
      "mortar_size": 0.07,
      "tile_grime": 0.4,
      "bump": 0.4
    },
    "church_stone_b": {
      "type": "brick",
      "color_a": "#9A968B",
      "color_b": "#85817A",
      "mortar": "#55524A",
      "brick_w": 2.0,
      "brick_h": 1.0,
      "mortar_size": 0.07,
      "tile_grime": 0.4,
      "bump": 0.4
    },
    "church_trim": {
      "type": "paint",
      "color": "#A8A394",
      "roughness": 0.8,
      "mottle": 0.08
    },
    "glass_blue": {
      "type": "paint",
      "color": "#27435A",
      "roughness": 0.05
    },
    "sign_green": {
      "type": "paint",
      "color": "#1F4A3A",
      "roughness": 0.5
    },
    "awning_red": {
      "type": "paint",
      "color": "#8E2A2A",
      "roughness": 0.8,
      "mottle": 0.06
    },
    "awning_blue": {
      "type": "paint",
      "color": "#25405E",
      "roughness": 0.8,
      "mottle": 0.06
    }
  },
  "wear": {
    "edge": 0.3,
    "grime": 0.5,
    "streaks": {
      "amount": 0.4,
      "color": "#3A332C"
    }
  },
  "avoid": [
    "showroom shine",
    "clean plastic look"
  ]
}
```
