"""
THROWAWAY SPIKE: shared pipeline for spec-driven assets.

Builders (cabinet, house, ...) make parts into PARTS[tag] = [objects], then call:
    meshes = join_parts(PARTS, spec, ctx)   # one mesh per tag, finish from spec["parts"][tag]
    bake(meshes, tex_dir, res_for)          # color / roughness / normal (+ metalness for metals)
    swap_to_baked(meshes)                   # preview uses ONLY the baked maps
    export_fbx(meshes, path)
"""

import math
import os
import time

import bpy
from mathutils import Vector


# ------------------------------------------------------------------ utils
def lin(hexstr):
    h = hexstr.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i : i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


def activate(o):
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o


def tag_grain(o):
    """Per-vertex one-hot 'grain' attribute along the part's longest side."""
    d = o.dimensions
    axis = max(range(3), key=lambda i: d[i])
    attr = o.data.color_attributes.new(name="grain", type="FLOAT_COLOR", domain="POINT")
    col = [0.0, 0.0, 0.0, 1.0]
    col[axis] = 1.0
    for item in attr.data:
        item.color = col


def use_gpu():
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        devs = [d for d in prefs.devices if d.type == "METAL"]
        for d in prefs.devices:
            d.use = d.type == "METAL"
        if devs:
            bpy.context.scene.cycles.device = "GPU"
            print(f"[pipeline] GPU: {[d.name for d in devs]}")
            return True
    except Exception as e:  # noqa
        print("[pipeline] GPU unavailable:", e)
    bpy.context.scene.cycles.device = "CPU"
    return False


# ------------------------------------------------------------------ finishes
def make_finish(name, f, wear, ctx):
    """Base recipe (wood / paint / metal / stone) + wear layers.
    ctx: {'W': width, 'H': height} for region-based layers (blood)."""
    skip = set(f.get("skip_wear", []))
    WEAR = {k: v for k, v in wear.items() if k not in skip}

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    N, L = mat.node_tree.nodes, mat.node_tree.links
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

    def lerp_f(a, b, t):
        return m("MULTIPLY_ADD", m("SUBTRACT", b, a), t, a)

    def lerp_c(a, b, t):
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

    def noise(scale_vec, scale, detail=6.0, rough=0.6, distortion=0.0):
        mp = N.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = scale_vec
        L.new(tc.outputs["Object"], mp.inputs["Vector"])
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

    def crevice(distance, samples=8):
        ao = N.new("ShaderNodeAmbientOcclusion")
        ao.inputs["Distance"].default_value = distance
        ao.samples = samples
        return m("SUBTRACT", 1.0, ao.outputs["AO"])

    bump_height, bump_strength = None, 0.0
    t = f["type"]

    if t == "wood":
        s = f.get("grain_scale", 1.0)
        attr = N.new("ShaderNodeAttribute")
        attr.attribute_name = "grain"
        wx, wy, wz = xyz(attr.outputs["Vector"])
        g = None
        for w, along in ((wx, 0), (wy, 1), (wz, 2)):
            cs, fs = [8 * s] * 3, [60 * s] * 3
            cs[along], fs[along] = 0.15 * s, 0.3 * s
            gi = m(
                "MULTIPLY_ADD",
                noise(cs, 2.5, 8, 0.65, 0.4),
                0.7,
                m("MULTIPLY", noise(fs, 3.0, 3), 0.3),
            )
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
        mottle = noise((1, 1, 1), 2.0, 6, 0.6)
        color = lerp_c(
            color, rgb("#000000"), m("MULTIPLY", m("SUBTRACT", mottle, 0.4), 0.12)
        )
        peel = noise((1, 1, 1), 300.0, 2)
        rough = m(
            "MULTIPLY_ADD", m("SUBTRACT", peel, 0.5), 0.05, f.get("roughness", 0.4)
        )
        metal = 0.0
        bump_height, bump_strength = peel, f.get("orange_peel", 0.02)
    elif t == "metal":
        color = rgb(f["color"])
        br = noise((1, 80, 80), 6.0, 4)
        rough = m(
            "MULTIPLY_ADD",
            m("SUBTRACT", br, 0.5),
            0.3 * f.get("brushed", 0.3),
            f.get("roughness", 0.4),
        )
        metal = 1.0
        bump_height, bump_strength = br, 0.05 * f.get("brushed", 0.3)
        if f.get("rust"):
            blotch = smooth(
                noise((1, 1, 1), 18.0, 8, 0.7), 0.55 - 0.15 * f["rust"], 0.62
            )
            rust = m(
                "MINIMUM",
                m(
                    "ADD",
                    m("MULTIPLY", blotch, f["rust"] * 1.4),
                    m("MULTIPLY", crevice(0.05), 2.0),
                ),
                1.0,
            )
            color = lerp_c(color, rgb(f.get("rust_color", "#5C2C14")), rust)
            rough = lerp_f(rough, 0.9, rust)
            metal = lerp_f(1.0, 0.0, rust)
            bump_height = m("ADD", bump_height, m("MULTIPLY", rust, 0.6))
            bump_strength = max(bump_strength, 0.12)
    elif t == "stone":
        mp = N.new("ShaderNodeMapping")
        L.new(tc.outputs["Object"], mp.inputs["Vector"])
        vo = N.new("ShaderNodeTexVoronoi")
        vo.feature = "DISTANCE_TO_EDGE"
        vo.inputs["Scale"].default_value = f.get("cell_scale", 1.0)
        L.new(mp.outputs["Vector"], vo.inputs["Vector"])
        edge = smooth(vo.outputs["Distance"], 0.0, 0.06)  # 0 at mortar, 1 inside stones
        tone = noise((1, 1, 1), 1.5, 4)
        color = lerp_c(rgb(f["color_b"]), rgb(f["color_a"]), tone)
        color = lerp_c(rgb(f["mortar"]), color, edge)
        rough = f.get("roughness", 0.85)
        metal = 0.0
        bump_height = m(
            "ADD", m("MULTIPLY", edge, 1.0), m("MULTIPLY", noise((1, 1, 1), 8, 6), 0.3)
        )
        bump_strength = f.get("bump", 0.3)
    else:
        raise ValueError(f"unknown finish type {t}")

    obj_x, obj_y, obj_z = xyz(tc.outputs["Object"])
    _, _, nz_ = xyz(tc.outputs["Normal"])

    # ---------------- wear layers
    if WEAR.get("water_stains"):
        field = noise((1, 1, 1), 1.2, 3, 0.5, 1.5)
        ring = m("SUBTRACT", smooth(field, 0.50, 0.53), smooth(field, 0.535, 0.56))
        stain = m(
            "MULTIPLY",
            m("ADD", ring, m("MULTIPLY", smooth(field, 0.5, 0.6), 0.35)),
            WEAR["water_stains"],
        )
        color = lerp_c(color, rgb("#1E140C"), m("MULTIPLY", stain, 0.6))

    if WEAR.get("streaks"):
        st = WEAR["streaks"]
        vertical = m("SUBTRACT", 1.0, smooth(m("ABSOLUTE", nz_), 0.2, 0.5))
        lines = smooth(noise((3, 3, 0.2), 1.5, 4, 0.5), 0.55, 0.78)
        mask = m("MULTIPLY", m("MULTIPLY", vertical, lines), st["amount"])
        color = lerp_c(color, rgb(st["color"]), m("MULTIPLY", mask, 0.45))

    if WEAR.get("grime"):
        crev = smooth(crevice(0.25, 16), 0.05, 0.6)
        grime = m(
            "MULTIPLY",
            m("MULTIPLY", crev, WEAR["grime"]),
            m("ADD", 0.5, noise((1, 1, 1), 12.0, 4)),
        )
        color = lerp_c(color, rgb("#120C08"), m("MINIMUM", grime, 0.9))
        rough = lerp_f(rough, 0.85, grime)

    if WEAR.get("edge") and f.get("edge_color"):
        bev = N.new("ShaderNodeBevel")
        bev.inputs["Radius"].default_value = 0.025
        bev.samples = 8
        geo = N.new("ShaderNodeNewGeometry")
        dot = N.new("ShaderNodeVectorMath")
        dot.operation = "DOT_PRODUCT"
        L.new(bev.outputs["Normal"], dot.inputs[0])
        L.new(geo.outputs["Normal"], dot.inputs[1])
        edge = smooth(m("SUBTRACT", 1.0, dot.outputs["Value"]), 0.01, 0.12)
        wear_m = m(
            "MULTIPLY",
            m("MULTIPLY", edge, smooth(noise((1, 1, 1), 25.0, 6, 0.7), 0.35, 0.6)),
            WEAR["edge"],
        )
        color = lerp_c(color, rgb(f["edge_color"]), wear_m)
        rough = lerp_f(rough, 0.7, wear_m)

    if WEAR.get("moss"):
        ms = WEAR["moss"]
        up = smooth(nz_, 0.3, 0.9)
        low = m("SUBTRACT", 1.0, smooth(obj_z, 0.3, 2.5))
        where = m(
            "MINIMUM",
            m(
                "ADD",
                m("ADD", m("MULTIPLY", up, 0.7), m("MULTIPLY", low, 0.8)),
                m("MULTIPLY", crevice(0.3), 1.2),
            ),
            1.0,
        )
        patchy = smooth(noise((1, 1, 1), 1.8, 8, 0.65), 0.42, 0.62)
        moss = m("MULTIPLY", m("MULTIPLY", where, patchy), ms["amount"])
        color = lerp_c(color, rgb(ms["color"]), moss)
        rough = lerp_f(rough, 0.95, moss)
        bump_height = m(
            "ADD",
            bump_height,
            m("MULTIPLY", moss, m("MULTIPLY", noise((1, 1, 1), 60, 4), 0.8)),
        )

    if WEAR.get("dust"):
        up = smooth(nz_, 0.55, 0.95)
        fine = smooth(noise((1, 1, 1), 3.0, 8, 0.5), 0.2, 0.7)
        dust = m("MULTIPLY", m("MULTIPLY", up, fine), WEAR["dust"])
        color = lerp_c(color, rgb(WEAR.get("dust_color", "#857E70")), dust)
        rough = lerp_f(rough, 0.95, dust)

    blood = WEAR.get("blood")
    if blood:
        W, H = ctx["W"], ctx["H"]
        rx, rz = blood["region"]["x"], blood["region"]["z"]
        jitter = m("MULTIPLY", m("SUBTRACT", noise((1, 1, 1), 3.0, 4), 0.5), 0.25)
        u = m("ADD", m("DIVIDE", m("ADD", obj_x, W / 2), W), jitter)
        v = m("ADD", m("DIVIDE", obj_z, H), jitter)
        region = m(
            "MULTIPLY",
            m(
                "MULTIPLY",
                smooth(u, rx[0] - 0.02, rx[0] + 0.05),
                m("SUBTRACT", 1.0, smooth(u, rx[1] - 0.08, rx[1])),
            ),
            m(
                "MULTIPLY",
                smooth(v, rz[0], rz[0] + 0.12),
                m("SUBTRACT", 1.0, smooth(v, rz[1] + 0.05, rz[1] + 0.1)),
            ),
        )
        drips = smooth(noise((14, 14, 0.5), 3.0, 4, 0.5), 0.55, 0.6)
        smear = m(
            "MULTIPLY",
            smooth(noise((1, 1, 1), 4.0, 6, 0.6, 0.8), 0.45, 0.5),
            smooth(v, rz[1] - 0.3, rz[1]),
        )
        mask = m(
            "MULTIPLY",
            m("MINIMUM", m("MULTIPLY", m("MAXIMUM", drips, smear), region), 1.0),
            blood["amount"],
        )
        color = lerp_c(color, rgb(blood["color"]), mask)
        rough = lerp_f(rough, 0.35, mask)

    metal = value(metal) if isinstance(metal, (int, float)) else metal
    if bump_height is not None:
        b = N.new("ShaderNodeBump")
        b.inputs["Strength"].default_value = min(bump_strength, 1.0)
        b.inputs["Distance"].default_value = 0.01
        L.new(bump_height, b.inputs["Height"])
        L.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    L.new(color, bsdf.inputs["Base Color"])
    L.new(rough, bsdf.inputs["Roughness"])
    L.new(metal, bsdf.inputs["Metallic"])
    return mat, {"color": color, "roughness": rough, "metalness": metal}, bsdf, out


# ------------------------------------------------------------------ join
def join_parts(PARTS, spec, ctx, prefix):
    """One mesh per tag. Returns list of dicts."""
    for objs in PARTS.values():
        for o in objs:
            tag_grain(o)
    meshes = []
    for tag, objs in PARTS.items():
        if not objs:
            continue
        fin = spec["parts"][tag]
        for o in objs:
            if o.modifiers:
                activate(o)
                for mod in list(o.modifiers):
                    bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.object.join()
        o = bpy.context.active_object
        o.name = o.data.name = f"{prefix}_{tag}"
        bpy.context.scene.cursor.location = (0, 0, 0)
        bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.01)
        bpy.ops.object.mode_set(mode="OBJECT")
        f = spec["finishes"][fin]
        mat, sockets, bsdf, out = make_finish(
            f"{tag}_{fin}_proc", f, spec.get("wear", {}), ctx
        )
        o.data.materials.clear()
        o.data.materials.append(mat)
        tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
        meshes.append(
            {
                "obj": o,
                "tag": tag,
                "finish": fin,
                "metal": f["type"] == "metal",
                "mat": mat,
                "sockets": sockets,
                "bsdf": bsdf,
                "out": out,
                "tris": tris,
            }
        )
        print(
            f"[pipeline] {o.name}: finish={fin} tris={tris}"
            + ("  OVER 20k!" if tris > 20000 else "")
        )
    return meshes


# ------------------------------------------------------------------ bake
def bake(meshes, tex_dir, res_for, samples=32):
    os.makedirs(tex_dir, exist_ok=True)
    bpy.context.scene.render.engine = "CYCLES"
    use_gpu()
    bpy.context.scene.cycles.samples = samples
    bpy.context.scene.render.bake.margin = 6
    t0 = time.time()
    for me in meshes:
        o, N, L = me["obj"], me["mat"].node_tree.nodes, me["mat"].node_tree.links
        activate(o)
        res = res_for(me["tag"])
        me["baked"] = {}
        kinds = ["color", "roughness", "normal"] + (
            ["metalness"] if me["metal"] else []
        )
        for kind in kinds:
            img = bpy.data.images.new(f"{o.name}_{kind}", res, res, alpha=False)
            if kind != "color":
                img.colorspace_settings.name = "Non-Color"
            tex = N.new("ShaderNodeTexImage")
            tex.image = img
            for n in N:
                n.select = False
            tex.select = True
            N.active = tex
            if kind == "normal":
                L.new(me["bsdf"].outputs["BSDF"], me["out"].inputs["Surface"])
                bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT")
            else:
                em = N.new("ShaderNodeEmission")
                L.new(me["sockets"][kind], em.inputs["Color"])
                L.new(em.outputs["Emission"], me["out"].inputs["Surface"])
                bpy.ops.object.bake(type="EMIT")
                N.remove(em)
            path = os.path.join(tex_dir, f"{o.name}_{kind}.png")
            img.filepath_raw = path
            img.file_format = "PNG"
            img.save()
            img.filepath = path
            me["baked"][kind] = img
            N.remove(tex)
        L.new(me["bsdf"].outputs["BSDF"], me["out"].inputs["Surface"])
        print(f"[pipeline] baked {o.name} ({res}px) t={time.time() - t0:.0f}s")
    return time.time() - t0


def swap_to_baked(meshes):
    for me in meshes:
        o = me["obj"]
        mt = bpy.data.materials.new(f"{o.name}_baked")
        mt.use_nodes = True
        N, L = mt.node_tree.nodes, mt.node_tree.links
        bsdf = N["Principled BSDF"]
        imgs = me["baked"]

        def tex(img):
            t = N.new("ShaderNodeTexImage")
            t.image = img
            return t

        L.new(tex(imgs["color"]).outputs["Color"], bsdf.inputs["Base Color"])
        L.new(tex(imgs["roughness"]).outputs["Color"], bsdf.inputs["Roughness"])
        if "metalness" in imgs:
            L.new(tex(imgs["metalness"]).outputs["Color"], bsdf.inputs["Metallic"])
        else:
            bsdf.inputs["Metallic"].default_value = 0.0
        nm = N.new("ShaderNodeNormalMap")
        L.new(tex(imgs["normal"]).outputs["Color"], nm.inputs["Color"])
        L.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
        o.data.materials.clear()
        o.data.materials.append(mt)


def export_fbx(meshes, path):
    bpy.ops.object.select_all(action="DESELECT")
    for me in meshes:
        me["obj"].select_set(True)
    bpy.ops.export_scene.fbx(
        filepath=path,
        use_selection=True,
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_UNITS",
        axis_forward="-Z",
        axis_up="Y",
        mesh_smooth_type="FACE",
        path_mode="COPY",
        embed_textures=True,
    )


def look(cam, target, loc, tgt, lens):
    cam.location = Vector(loc)
    target.location = Vector(tgt)
    cam.data.lens = lens
