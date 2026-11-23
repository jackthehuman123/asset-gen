"""What a builder's build(params, rng) returns. bpy-free.

parts: {part_tag: [bpy Object, ...]}
shots: [(name, cam_location, target, lens), ...]
ctx:   {"W": float, "H": float} (overall width and height, for finishes)
"""

from collections import namedtuple

BuildResult = namedtuple("BuildResult", "parts shots ctx")
