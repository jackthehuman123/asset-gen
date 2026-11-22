"""
THROWAWAY SPIKE: style spec -> Blender -> baked PBR maps -> Roblox-ready FBX.

  blender -b --factory-startup -P cabinet_styled.py -- <spec.json> <out_dir>

1. Build the cabinet from the spec's dimensions, as named parts
   (top, carcass, fronts, handles, legs, foot_caps).
2. Each part gets the finish the spec assigns (wood / paint / metal recipes).
3. Parts sharing a finish are joined into one mesh (one Roblox MeshPart each).
4. Bake color / normal / roughness / metalness maps per mesh (for SurfaceAppearance).
5. Export FBX with embedded textures + render previews of the BAKED result.

Units: 1 Blender unit = 1 stud.
"""
import json
import math
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
SPEC_PATH, OUT = argv[0], argv[1]
TEX_DIR = os.path.join(OUT, "textures")
os.makedirs(TEX_DIR, exist_ok=True)
spec = json.load(open(SPEC_PATH))
dims = spec.get("dimensions", {})
RES = 1024

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ------------------------------------------------------------------ geometry
W = dims.get("width", 4.2)
D = dims.get("depth", 1.6)
LEG_H = dims.get("leg_height", 0.55)
BODY_H = dims.get("body_height", 2.45)
DRAWER_COL_W = dims.get("drawer_column_width", 1.4)
PANEL_T, GAP, FRAME, BEVEL = 0.06, 0.025, 0.06, 0.012

PARTS = {k: [] for k in ("top", "carcass", "fronts", "handles", "legs", "foot_caps")}


def box(tag, size, loc, bevel=BEVEL):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        m = o.modifiers.new("Bevel", "BEVEL")
        m.width, m.segments, m.limit_method = bevel, 2, "ANGLE"
    PARTS[tag].append(o)
    return o


def cyl(tag, r, depth, loc, rot, verts=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    PARTS[tag].append(bpy.context.active_object)


def handle(length, center, vertical):
    x, y, z = center
    rot = (0, 0, 0) if vertical else (0, math.pi / 2, 0)
    cyl("handles", 0.022, length, (x, y - 0.09, z), rot)
    for s in (-1, 1):
        off = s * (length / 2 - 0.05)
        loc = (x, y - 0.045, z + off) if vertical else (x + off, y - 0.045, z)
        cyl("handles", 0.016, 0.09, loc, (math.pi / 2, 0, 0), verts=12)


z0, front_y = LEG_H, -D / 2
box("top", (W + 0.08, D + 0.06, 0.08), (0, 0, z0 + BODY_H - 0.04))
box("carcass", (W, D, 0.08), (0, 0, z0 + 0.04))
box("carcass", (0.06, D, BODY_H - 0.16), (-W / 2 + 0.03, 0, z0 + BODY_H / 2))
box("carcass", (0.06, D, BODY_H - 0.16), (W / 2 - 0.03, 0, z0 + BODY_H / 2))
box("carcass", (W - 0.12, 0.04, BODY_H - 0.16), (0, D / 2 - 0.02, z0 + BODY_H / 2))
divider_x = -W / 2 + FRAME + DRAWER_COL_W
box("carcass", (0.05, D - 0.06, BODY_H - 0.16), (divider_x, -0.02, z0 + BODY_H / 2))
box("carcass", (W - 0.12, 0.05, 0.06), (0, front_y + 0.06, z0 + 0.11))

inner_bottom, inner_top = z0 + 0.14, z0 + BODY_H - 0.1
inner_h = inner_top - inner_bottom
fy = front_y - PANEL_T / 2 + 0.01

x0, x1 = -W / 2 + FRAME, divider_x - 0.025
z = inner_top
for r in (0.28, 0.33, 0.39):
    h = inner_h * r
    cz = z - h / 2
    box("fronts", (x1 - x0 - GAP, PANEL_T, h - GAP), ((x0 + x1) / 2, fy, cz))
    handle(min(0.6, (x1 - x0) * 0.4), ((x0 + x1) / 2, fy - PANEL_T / 2, cz + h * 0.18), vertical=False)
    z -= h

dx0, dx1 = divider_x + 0.025, W / 2 - FRAME
door_w = (dx1 - dx0) / 2
for i in range(2):
    cx = dx0 + door_w * (i + 0.5)
    box("fronts", (door_w - GAP, PANEL_T, inner_h - GAP), (cx, fy, inner_bottom + inner_h / 2))
    box("fronts", (door_w - 0.3, 0.012, inner_h - 0.3), (cx, fy - PANEL_T / 2 - 0.004, inner_bottom + inner_h / 2),
        bevel=0.004)
    hx = cx + (door_w / 2 - 0.14) * (1 if i == 0 else -1)
    handle(inner_h * 0.42, (hx, fy - PANEL_T / 2, inner_bottom + inner_h * 0.55), vertical=True)

for sx in (-1, 1):
    for sy in (-1, 1):
        lx, ly = sx * (W / 2 - 0.22), sy * (D / 2 - 0.2)
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.035, radius2=0.075, depth=LEG_H + 0.02,
                                        location=(lx, ly, LEG_H / 2))
        leg = bpy.context.active_object
        leg.rotation_euler = (-sy * math.radians(6), sx * math.radians(6), 0)
        PARTS["legs"].append(leg)
        tilt = math.tan(math.radians(6)) * LEG_H / 2
        cyl("foot_caps", 0.038, 0.04, (lx - sx * tilt, ly - sy * tilt, 0.02), (0, 0, 0))


# ------------------------------------------------------------------ finishes
H_TOTAL = LEG_H + BODY_H
WEAR = spec.get("wear", {})


def lin(hexstr):
    h = hexstr.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


def make_finish(name, f):
    """Base recipe (wood / paint / metal) + wear layers from spec['wear'].
    Returns (material, {'color','roughness','metalness'} -> socket, bsdf, output)."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    N, L = nt.nodes, nt.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    bsdf = N.new("ShaderNodeBsdfPrincipled")
    L.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    def link_or_set(sock, v):
        if isinstance(v, (int, float)):
            sock.default_value = v
        else:
            L.new(v, sock)

    def value(v):
        n = N.new("ShaderNodeValue")
        n.outputs[0].default_value = v
        return n.outputs[0]

    def rgb(hexstr):
        n = N.new("ShaderNodeRGB")
        n.outputs[0].default_value = lin(hexstr)
        return n.outputs[0]

    def m(op, a, b=None, c=None):
        n = N.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, b, c)):
            if v is not None:
                link_or_set(n.inputs[i], v)
        return n.outputs[0]

    def smooth(v, lo, hi):
        n = N.new("ShaderNodeMapRange")
        n.interpolation_type = "SMOOTHSTEP"
        link_or_set(n.inputs["Value"], v)
        n.inputs["From Min"].default_value = lo
        n.inputs["From Max"].default_value = hi
        return n.outputs["Result"]

    def lerp_f(a, b, t):  # a + (b - a) * t
        return m("MULTIPLY_ADD", m("SUBTRACT", b, a), t, a)

    def lerp_c(a, b, t):  # colour lerp with vector math
        d = N.new("ShaderNodeVectorMath")
        d.operation = "SUBTRACT"
        L.new(b, d.inputs[0])
        L.new(a, d.inputs[1])
        s = N.new("ShaderNodeVectorMath")
        s.operation = "SCALE"
        L.new(d.outputs[0], s.inputs[0])
        link_or_set(s.inputs[3], t)
        ad = N.new("ShaderNodeVectorMath")
        ad.operation = "ADD"
        L.new(a, ad.inputs[0])
        L.new(s.outputs[0], ad.inputs[1])
        return ad.outputs[0]

    tc = N.new("ShaderNodeTexCoord")

    def noise(scale_vec, scale, detail=6.0, rough=0.6, distortion=0.0, coord="Object"):
        mp = N.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = scale_vec
        L.new(tc.outputs[coord], mp.inputs["Vector"])
        nz = N.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = scale
        nz.inputs["Detail"].default_value = detail
        nz.inputs["Roughness"].default_value = rough
        nz.inputs["Distortion"].default_value = distortion
        L.new(mp.outputs["Vector"], nz.inputs["Vector"])
        return nz.outputs["Fac"]

    def xyz(sock):
        n = N.new("ShaderNodeSeparateXYZ")
        L.new(sock, n.inputs[0])
        return n.outputs["X"], n.outputs["Y"], n.outputs["Z"]

    bump_height = None
    bump_strength = 0.0
    t = f["type"]

    # ---------------- base recipes
    if t == "wood":
        s = f.get("grain_scale", 1.0)
        attr = N.new("ShaderNodeAttribute")
        attr.attribute_name = "grain"
        wx, wy, wz = xyz(attr.outputs["Vector"])
        g = None
        for w, along in ((wx, 0), (wy, 1), (wz, 2)):
            coarse_scale = [8 * s] * 3
            fine_scale = [60 * s] * 3
            coarse_scale[along] = 0.15 * s
            fine_scale[along] = 0.3 * s
            gi = m("MULTIPLY_ADD", noise(coarse_scale, 2.5, 8, 0.65, 0.4), 0.7,
                   m("MULTIPLY", noise(fine_scale, 3.0, 3), 0.3))
            term = m("MULTIPLY", gi, w)
            g = term if g is None else m("ADD", g, term)
        ramp = N.new("ShaderNodeValToRGB")
        k = f.get("grain_contrast", 0.5)
        ramp.color_ramp.elements[0].position = 0.5 - 0.2 * k
        ramp.color_ramp.elements[1].position = 0.5 + 0.2 * k
        ramp.color_ramp.elements[0].color = lin(f["grain"])
        ramp.color_ramp.elements[1].color = lin(f["base"])
        L.new(g, ramp.inputs["Fac"])
        color = ramp.outputs["Color"]
        rough = m("MULTIPLY_ADD", m("SUBTRACT", g, 0.5), 0.2, f.get("roughness", 0.5))
        metal = 0.0
        bump_height, bump_strength = g, f.get("bump", 0.1)
    elif t == "paint":
        color = rgb(f["color"])
        peel = noise((1, 1, 1), 400.0, 2)
        rough = m("MULTIPLY_ADD", m("SUBTRACT", peel, 0.5), 0.05, f.get("roughness", 0.4))
        metal = 0.0
        bump_height, bump_strength = peel, f.get("orange_peel", 0.02)
    elif t == "metal":
        color = rgb(f["color"])
        br = noise((1, 80, 80), 6.0, 4)
        rough = m("MULTIPLY_ADD", m("SUBTRACT", br, 0.5), 0.3 * f.get("brushed", 0.3), f.get("roughness", 0.4))
        metal = 1.0
        bump_height, bump_strength = br, 0.05 * f.get("brushed", 0.3)
        if f.get("rust"):
            ao = N.new("ShaderNodeAmbientOcclusion")
            ao.inputs["Distance"].default_value = 0.05
            crev = m("SUBTRACT", 1.0, ao.outputs["AO"])
            blotch = smooth(noise((1, 1, 1), 18.0, 8, 0.7), 0.55 - 0.15 * f["rust"], 0.62)
            rust = m("MINIMUM", m("ADD", m("MULTIPLY", blotch, f["rust"] * 1.4), m("MULTIPLY", crev, 2.0)), 1.0)
            color = lerp_c(color, rgb(f.get("rust_color", "#5C2C14")), rust)
            rough = lerp_f(rough, 0.9, rust)
            metal = lerp_f(1.0, 0.0, rust)
            bump_height = m("ADD", bump_height, m("MULTIPLY", rust, 0.6))
            bump_strength = max(bump_strength, 0.12)
    else:
        raise ValueError(f"unknown finish type {t}")

    obj_x, obj_y, obj_z = xyz(tc.outputs["Object"])
    nx, ny, nz_ = xyz(tc.outputs["Normal"])

    # ---------------- wear layers (only if the spec asks for them)
    if WEAR.get("water_stains"):
        w = WEAR["water_stains"]
        field = noise((1, 1, 1), 1.2, 3, 0.5, 1.5)
        ring = m("SUBTRACT", smooth(field, 0.50, 0.53), smooth(field, 0.535, 0.56))
        inside = m("MULTIPLY", smooth(field, 0.5, 0.6), 0.35)
        stain = m("MULTIPLY", m("ADD", ring, inside), w)
        color = lerp_c(color, rgb("#1E140C"), m("MULTIPLY", stain, 0.6))

    if WEAR.get("grime"):
        ao = N.new("ShaderNodeAmbientOcclusion")
        ao.inputs["Distance"].default_value = 0.25
        ao.samples = 16
        crev = smooth(m("SUBTRACT", 1.0, ao.outputs["AO"]), 0.05, 0.6)
        grime = m("MULTIPLY", m("MULTIPLY", crev, WEAR["grime"]), m("ADD", 0.5, noise((1, 1, 1), 12.0, 4)))
        color = lerp_c(color, rgb("#120C08"), m("MINIMUM", grime, 0.9))
        rough = lerp_f(rough, 0.85, grime)

    if WEAR.get("edge") and f.get("edge_color"):
        bev = N.new("ShaderNodeBevel")
        bev.inputs["Radius"].default_value = 0.025
        geo = N.new("ShaderNodeNewGeometry")
        dot = N.new("ShaderNodeVectorMath")
        dot.operation = "DOT_PRODUCT"
        L.new(bev.outputs["Normal"], dot.inputs[0])
        L.new(geo.outputs["Normal"], dot.inputs[1])
        edge = smooth(m("SUBTRACT", 1.0, dot.outputs["Value"]), 0.01, 0.12)
        breakup = smooth(noise((1, 1, 1), 25.0, 6, 0.7), 0.35, 0.6)
        wear = m("MULTIPLY", m("MULTIPLY", edge, breakup), WEAR["edge"])
        color = lerp_c(color, rgb(f["edge_color"]), wear)
        rough = lerp_f(rough, 0.7, wear)

    if WEAR.get("dust"):
        up = smooth(nz_, 0.55, 0.95)
        patchy = smooth(noise((1, 1, 1), 6.0, 6, 0.6), 0.3, 0.65)
        dust = m("MULTIPLY", m("MULTIPLY", up, patchy), WEAR["dust"])
        color = lerp_c(color, rgb(WEAR.get("dust_color", "#857E70")), dust)
        rough = lerp_f(rough, 0.95, dust)
        if t == "metal":
            metal = lerp_f(metal, 0.0, dust)

    blood = WEAR.get("blood")
    if blood:
        rx, rz = blood["region"]["x"], blood["region"]["z"]
        jitter = m("MULTIPLY", m("SUBTRACT", noise((1, 1, 1), 3.0, 4), 0.5), 0.25)
        u = m("ADD", m("DIVIDE", m("ADD", obj_x, W / 2), W), jitter)
        v = m("ADD", m("DIVIDE", obj_z, H_TOTAL), jitter)
        region = m("MULTIPLY",
                   m("MULTIPLY", smooth(u, rx[0] - 0.02, rx[0] + 0.05), m("SUBTRACT", 1.0, smooth(u, rx[1] - 0.08, rx[1]))),
                   m("MULTIPLY", smooth(v, rz[0], rz[0] + 0.12), m("SUBTRACT", 1.0, smooth(v, rz[1] + 0.05, rz[1] + 0.1))))
        drips = smooth(noise((14, 14, 0.5), 3.0, 4, 0.5), 0.55, 0.6)
        # drips get denser toward the top of the region (smear source)
        source = smooth(v, rz[1] - 0.3, rz[1])
        smear = m("MULTIPLY", smooth(noise((1, 1, 1), 4.0, 6, 0.6, 0.8), 0.45, 0.5), source)
        mask = m("MINIMUM", m("MULTIPLY", m("MAXIMUM", drips, smear), region), 1.0)
        mask = m("MULTIPLY", mask, blood["amount"])
        color = lerp_c(color, rgb(blood["color"]), mask)
        rough = lerp_f(rough, 0.35, mask)
        if t == "metal":
            metal = lerp_f(metal, 0.0, mask)

    metal = value(metal) if isinstance(metal, (int, float)) else metal
    if bump_height is not None:
        b = N.new("ShaderNodeBump")
        b.inputs["Strength"].default_value = bump_strength
        b.inputs["Distance"].default_value = 0.01
        L.new(bump_height, b.inputs["Height"])
        L.new(b.outputs["Normal"], bsdf.inputs["Normal"])

    L.new(color, bsdf.inputs["Base Color"])
    L.new(rough, bsdf.inputs["Roughness"])
    L.new(metal, bsdf.inputs["Metallic"])
    return mat, {"color": color, "roughness": rough, "metalness": metal}, bsdf, out


# ------------------------------------------------------------------ join by finish
def activate(o):
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o


def tag_grain(o):
    d = o.dimensions
    axis = max(range(3), key=lambda i: d[i])
    attr = o.data.color_attributes.new(name="grain", type="FLOAT_COLOR", domain="POINT")
    col = [0.0, 0.0, 0.0, 1.0]
    col[axis] = 1.0
    for item in attr.data:
        item.color = col


for objs in PARTS.values():
    for o in objs:
        tag_grain(o)

groups = {}
for tag, objs in PARTS.items():
    groups.setdefault(spec["parts"][tag], []).extend(objs)

meshes = []
for fin, objs in groups.items():
    for o in objs:
        activate(o)
        for m in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    o.name = o.data.name = f"Cabinet_{fin}"
    scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    # UVs for baking
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    mat, sockets, bsdf, out = make_finish(f"{fin}_proc", spec["finishes"][fin])
    o.data.materials.clear()
    o.data.materials.append(mat)
    meshes.append((o, fin, mat, sockets, bsdf, out))
    tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
    print(f"[styled] {o.name}: tris={tris}")

# ------------------------------------------------------------------ bake
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 64 if spec.get("wear") else 16
scene.render.bake.margin = 8

baked = {}
for o, fin, mat, sockets, bsdf, out in meshes:
    activate(o)
    N, L = mat.node_tree.nodes, mat.node_tree.links
    baked[o.name] = {}
    for kind in ("color", "roughness", "metalness", "normal"):
        img = bpy.data.images.new(f"{o.name}_{kind}", RES, RES, alpha=False)
        if kind != "color":
            img.colorspace_settings.name = "Non-Color"
        tex = N.new("ShaderNodeTexImage")
        tex.image = img
        for n in N:
            n.select = False
        tex.select = True
        N.active = tex
        if kind == "normal":
            L.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
            bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT")
        else:
            em = N.new("ShaderNodeEmission")
            L.new(sockets[kind], em.inputs["Color"])
            L.new(em.outputs["Emission"], out.inputs["Surface"])
            bpy.ops.object.bake(type="EMIT")
            N.remove(em)
        path = os.path.join(TEX_DIR, f"{o.name}_{kind}.png")
        img.filepath_raw = path
        img.file_format = "PNG"
        img.save()
        img.filepath = path
        baked[o.name][kind] = img
        N.remove(tex)
    L.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    print(f"[styled] baked {o.name}")

# Swap to materials that use ONLY the baked images (what Roblox will see)
for o, fin, *_ in meshes:
    m = bpy.data.materials.new(f"{o.name}_baked")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    bsdf = N["Principled BSDF"]
    imgs = baked[o.name]

    def tex(img):
        t = N.new("ShaderNodeTexImage")
        t.image = img
        return t

    L.new(tex(imgs["color"]).outputs["Color"], bsdf.inputs["Base Color"])
    L.new(tex(imgs["roughness"]).outputs["Color"], bsdf.inputs["Roughness"])
    L.new(tex(imgs["metalness"]).outputs["Color"], bsdf.inputs["Metallic"])
    nm = N.new("ShaderNodeNormalMap")
    L.new(tex(imgs["normal"]).outputs["Color"], nm.inputs["Color"])
    L.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    o.data.materials.clear()
    o.data.materials.append(m)

# ------------------------------------------------------------------ export
bpy.ops.object.select_all(action="DESELECT")
for o, *_ in meshes:
    o.select_set(True)
bpy.ops.export_scene.fbx(
    filepath=os.path.join(OUT, "cabinet_styled.fbx"),
    use_selection=True,
    apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_UNITS",
    axis_forward="-Z",
    axis_up="Y",
    mesh_smooth_type="FACE",
    path_mode="COPY",
    embed_textures=True,
)

# ------------------------------------------------------------------ preview scene (not exported)
def plain(name, hexstr, rough=0.8):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = lin(hexstr)
    b.inputs["Roughness"].default_value = rough
    return m


def prop(size, loc, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.scale = size
    o.data.materials.append(mat)


ABANDONED = bool(spec.get("wear"))
if ABANDONED:  # dim, dusty Japanese room: dirty plaster wall, old tatami, cold window light
    wall, floor = plain("Wall", "#857D6E", 0.95), plain("Floor", "#77704F", 0.9)
    bg, bg_strength = (0.55, 0.6, 0.7, 1), 0.08
else:  # bright white modern living room
    wall, floor = plain("Wall", "#F4F2EE", 0.9), plain("Floor", "#D9CBB6", 0.6)
    bg, bg_strength = (0.9, 0.9, 0.92, 1), 0.6
prop((30, 30, 0.1), (0, 0, -0.05), floor)
prop((30, 0.1, 12), (0, D / 2 + 0.6, 6), wall)
top_z = LEG_H + BODY_H
tv_w = W * 0.75
prop((tv_w, 0.08, tv_w * 9 / 16), (0, 0.15, top_z + 0.12 + tv_w * 9 / 32), plain("TV", "#0B0B0C", 0.2))
prop((0.9, 0.5, 0.04), (0, 0.15, top_z + 0.02), plain("TVStand", "#1A1A1A", 0.4))
prop((0.12, 0.12, 0.12), (0, 0.15, top_z + 0.08), plain("TVNeck", "#1A1A1A", 0.4))

world = bpy.data.worlds.new("World")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = bg
world.node_tree.nodes["Background"].inputs["Strength"].default_value = bg_strength
scene.world = world

bpy.ops.object.light_add(type="AREA", location=(-5, -6, 6))
key = bpy.context.active_object
key.data.size = 5
key.rotation_euler = (math.radians(50), 0, math.radians(-40))
if ABANDONED:
    key.data.energy = 500
    key.data.color = (0.75, 0.82, 1.0)
    bpy.ops.object.light_add(type="POINT", location=(3, -2.5, 2.5))
    fill = bpy.context.active_object
    fill.data.energy = 25
    fill.data.color = (1.0, 0.75, 0.5)
else:
    key.data.energy = 900

cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
scene.collection.objects.link(cam)
target = bpy.data.objects.new("Target", None)
scene.collection.objects.link(target)
c = cam.constraints.new("TRACK_TO")
c.target, c.track_axis, c.up_axis = target, "TRACK_NEGATIVE_Z", "UP_Y"
scene.camera = cam

scene.cycles.samples = 96
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = 1200, 900

for name, cam_loc, tgt, lens in (
    ("preview_wide", (-W * 1.05, -W * 1.6, 3.4), (0, 0, H_TOTAL * 0.6 + 0.5), 40),
    ("preview_close", (-W / 2 + DRAWER_COL_W * 0.5 - 0.9, -D / 2 - 2.3, LEG_H + BODY_H * 0.65 + 0.7),
     (-W / 2 + DRAWER_COL_W * 0.5, -D / 2, LEG_H + BODY_H * 0.6), 50),
):
    cam.location = cam_loc
    target.location = tgt
    cam.data.lens = lens
    scene.render.filepath = os.path.join(OUT, f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print(f"[styled] rendered {name}")

print("[styled] done ->", OUT)
