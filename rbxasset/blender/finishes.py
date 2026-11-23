"""Procedural finish recipes (wood / paint / metal / stone / brick / siding + wear layers). Runs inside Blender."""

from collections import namedtuple

import bpy

FinishNodes = namedtuple("FinishNodes", "mat sockets bsdf out")


def lin(hexstr):
    h = hexstr.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i : i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


def make_finish(name, f, wear, ctx, tile=None):
    """Base recipe (wood / paint / metal / stone) + wear layers.

    ctx: dict from the caller (e.g. {'W': width, 'H': height}); no layer reads it
    now that blood is a Decal, kept for position-based layers.
    tile: tile size in studs. When set, every noise / Voronoi reads the bake plane's
    UV mapped onto a 4D torus (periodic in u and v); geometry/position layers
    (grime, edge, moss up/low/crevice, dust, rust crevice) are skipped. Moss is skipped
    in tile mode unless the finish sets `tile_moss` (0-1), used as a low constant mask."""
    import math

    tiled = tile is not None
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

    def coord():
        return tc.outputs["Object"]

    uv_cache = {}

    def torus(sx, sy):
        """(vector, w) sockets for a 4D torus with U/V frequencies sx, sy per tile."""
        if "uv" not in uv_cache:
            uvn = N.new("ShaderNodeTexCoord")
            sep = N.new("ShaderNodeSeparateXYZ")
            L.new(uvn.outputs["UV"], sep.inputs[0])
            uv_cache["uv"] = (sep.outputs["X"], sep.outputs["Y"])
        u, v = uv_cache["uv"]
        k = 2 * math.pi
        a, b = m("MULTIPLY", u, k), m("MULTIPLY", v, k)
        rx, ry = tile * sx / k, tile * sy / k
        comb = N.new("ShaderNodeCombineXYZ")
        L.new(m("MULTIPLY", m("COSINE", a), rx), comb.inputs["X"])
        L.new(m("MULTIPLY", m("SINE", a), rx), comb.inputs["Y"])
        L.new(m("MULTIPLY", m("COSINE", b), ry), comb.inputs["Z"])
        return comb.outputs["Vector"], m("MULTIPLY", m("SINE", b), ry)

    def tex4d(node, sx, sy):
        node.inputs["Scale"].default_value = 1.0
        vec, w = torus(sx, sy)
        L.new(vec, node.inputs["Vector"])
        L.new(w, node.inputs["W"])

    def noise(scale_vec, scale, detail=6.0, rough=0.6, distortion=0.0, uv=None):
        """uv=(sx, sy): tile-mode axis scales (default: first two of scale_vec)."""
        if tiled:
            sx, sy = uv or scale_vec[:2]
            nz = N.new("ShaderNodeTexNoise")
            nz.noise_dimensions = "4D"
            nz.inputs["Detail"].default_value = detail
            nz.inputs["Roughness"].default_value = rough
            nz.inputs["Distortion"].default_value = distortion
            tex4d(nz, sx * scale, sy * scale)
            return nz.outputs["Fac"]
        mp = N.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = scale_vec
        L.new(coord(), mp.inputs["Vector"])
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
        if tiled:  # grain axis is U
            cs, fs = [0.15 * s, 8 * s, 8 * s], [0.3 * s, 60 * s, 60 * s]
            g = m(
                "MULTIPLY_ADD",
                noise(cs, 2.5, 8, 0.65, 0.4),
                0.7,
                m("MULTIPLY", noise(fs, 3.0, 3), 0.3),
            )
        else:
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
        if f.get("mottle"):
            patch = smooth(noise((1, 1, 1), 1.2, 4, 0.5), 0.3, 0.7)
            # age discoloration: a darker, yellowed version of the paint's own colour
            # (a fixed grey-brown target read as green-grey mould on pale plaster)
            if f.get("mottle_color"):
                target = rgb(f["mottle_color"])
            else:
                yel = N.new("ShaderNodeVectorMath")
                yel.operation = "MULTIPLY"
                L.new(color, yel.inputs[0])
                yel.inputs[1].default_value = (0.78, 0.68, 0.45)
                target = yel.outputs[0]
            color = lerp_c(color, target, m("MULTIPLY", patch, 0.5 * f["mottle"]))
        if f.get("cracks"):
            vc = N.new("ShaderNodeTexVoronoi")
            vc.feature = "DISTANCE_TO_EDGE"
            vc.inputs["Scale"].default_value = 3.0
            if tiled:
                vc.voronoi_dimensions = "4D"
                tex4d(vc, 3.0, 3.0)
            else:
                wob = N.new("ShaderNodeMapping")
                L.new(coord(), wob.inputs["Vector"])
                L.new(wob.outputs["Vector"], vc.inputs["Vector"])
            line = m("SUBTRACT", 1.0, smooth(vc.outputs["Distance"], 0.0, 0.015))
            color = lerp_c(color, rgb("#1a1510"), m("MULTIPLY", line, f["cracks"]))
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
            crev_rust = 0.0 if tiled else m("MULTIPLY", crevice(0.05), 2.0)
            blotch = smooth(
                noise((1, 1, 1), 18.0, 8, 0.7), 0.55 - 0.15 * f["rust"], 0.62
            )
            rust = m(
                "MINIMUM",
                m("ADD", m("MULTIPLY", blotch, f["rust"] * 1.4), crev_rust),
                1.0,
            )
            color = lerp_c(color, rgb(f.get("rust_color", "#5C2C14")), rust)
            rough = lerp_f(rough, 0.9, rust)
            metal = lerp_f(1.0, 0.0, rust)
            bump_height = m("ADD", bump_height, m("MULTIPLY", rust, 0.6))
            bump_strength = max(bump_strength, 0.12)
    elif t == "stone":
        vo = N.new("ShaderNodeTexVoronoi")
        vo.feature = "DISTANCE_TO_EDGE"
        if tiled:
            vo.voronoi_dimensions = "4D"
            cs_ = f.get("cell_scale", 1.0)
            tex4d(vo, cs_, cs_)
        else:
            mp = N.new("ShaderNodeMapping")
            L.new(coord(), mp.inputs["Vector"])
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
    elif t in ("brick", "siding"):
        # Pattern lines run along U (tiled: tile UV, whole bricks/boards per tile so it repeats;
        # untiled: studs, u = x + y, v = z). Colour comes from the node, bump from its mask.
        if tiled:
            vec = N.new("ShaderNodeTexCoord").outputs["UV"]
        else:
            ox, oy, oz = xyz(coord())
            cb = N.new("ShaderNodeCombineXYZ")
            L.new(m("ADD", ox, oy), cb.inputs["X"])
            L.new(oz, cb.inputs["Y"])
            vec = cb.outputs["Vector"]
        if t == "brick":
            bw, bh, ms = (
                f.get("brick_w", 0.75),
                f.get("brick_h", 0.25),
                f.get("mortar_size", 0.035),
            )
            if tiled:
                ncol = max(2, round(tile / bw))
                nrow = max(2, round(tile / bh))
                nrow += nrow % 2
                bw, bh, ms = 1.0 / ncol, 1.0 / nrow, ms / tile
            bk = N.new("ShaderNodeTexBrick")
            bk.offset, bk.offset_frequency = 0.5, 2
            bk.inputs["Color1"].default_value = lin(f["color_a"])
            bk.inputs["Color2"].default_value = lin(f["color_b"])
            bk.inputs["Mortar"].default_value = lin(f["mortar"])
            bk.inputs["Scale"].default_value = 1.0
            bk.inputs["Mortar Size"].default_value = ms
            bk.inputs["Mortar Smooth"].default_value = 0.1
            bk.inputs["Brick Width"].default_value = bw
            bk.inputs["Row Height"].default_value = bh
            L.new(vec, bk.inputs["Vector"])
            tone = smooth(noise((1, 1, 1), 2.0, 4), 0.3, 0.7)
            color = lerp_c(
                bk.outputs["Color"], rgb("#000000"), m("MULTIPLY", tone, 0.12)
            )
            rough = f.get("roughness", 0.85)
            bump_height, bump_strength = bk.outputs["Fac"], f.get("bump", 0.4)
        else:
            bh = f.get("board_h", 0.5)
            n = max(2, round(tile / bh)) if tiled else 1.0 / bh
            sep = N.new("ShaderNodeSeparateXYZ")
            L.new(vec, sep.inputs[0])
            vv = m("MULTIPLY", sep.outputs["Y"], n)
            frac = m("FRACT", vv)
            idx = m("FLOOR", vv)
            wn = N.new("ShaderNodeTexWhiteNoise")
            wn.noise_dimensions = "1D"
            L.new(idx, wn.inputs["W"])
            groove = m("SUBTRACT", 1.0, smooth(frac, 0.0, 0.08))
            shade = m(
                "SUBTRACT",
                1.0,
                m(
                    "MULTIPLY",
                    m("ADD", groove, m("MULTIPLY", wn.outputs["Value"], 0.2)),
                    0.45,
                ),
            )
            color = lerp_c(rgb("#000000"), rgb(f["color"]), shade)
            rough = f.get("roughness", 0.6)
            bump_height, bump_strength = m("SUBTRACT", 1.0, groove), f.get("bump", 0.5)
        metal = 0.0
    else:
        raise ValueError(f"unknown finish type {t}")

    if not tiled:
        _, _, obj_z = xyz(coord())
        _, _, nz_ = xyz(tc.outputs["Normal"])

    # ---------------- wear layers
    if tiled and f.get(
        "tile_grime"
    ):  # tiles carry no position cues: a patchy dirt film everywhere
        film = smooth(noise((1, 1, 1), 1.5, 6), 0.35, 0.7)
        color = lerp_c(
            color, rgb("#15110d"), m("MULTIPLY", film, 0.5 * f["tile_grime"])
        )

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
        vertical = (
            1.0 if tiled else m("SUBTRACT", 1.0, smooth(m("ABSOLUTE", nz_), 0.2, 0.5))
        )
        lines = smooth(noise((3, 3, 0.2), 1.5, 4, 0.5, uv=(3, 0.2)), 0.55, 0.78)
        mask = m("MULTIPLY", m("MULTIPLY", vertical, lines), st["amount"])
        color = lerp_c(color, rgb(st["color"]), m("MULTIPLY", mask, 0.45))

    if WEAR.get("grime") and not tiled:
        crev = smooth(crevice(0.25, 16), 0.05, 0.6)
        grime = m(
            "MULTIPLY",
            m("MULTIPLY", crev, WEAR["grime"]),
            m("ADD", 0.5, noise((1, 1, 1), 12.0, 4)),
        )
        color = lerp_c(color, rgb("#120C08"), m("MINIMUM", grime, 0.9))
        rough = lerp_f(rough, 0.85, grime)

    if WEAR.get("edge") and f.get("edge_color") and not tiled:
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

    tile_moss = f.get("tile_moss", 0.0) if tiled else None
    if WEAR.get("moss") and (not tiled or tile_moss):
        ms = WEAR["moss"]
        if tiled:
            where = float(tile_moss)  # low constant: tiles carry no position cues
        else:
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

    if WEAR.get("dust") and not tiled:
        up = smooth(nz_, 0.55, 0.95)
        fine = smooth(noise((1, 1, 1), 40.0, 4, 0.5), 0.3, 0.6)  # fine, even film
        dust = m(
            "MULTIPLY",
            m("MULTIPLY", up, m("ADD", 0.6, m("MULTIPLY", fine, 0.4))),
            WEAR["dust"],
        )
        color = lerp_c(color, rgb(WEAR.get("dust_color", "#857E70")), dust)
        rough = lerp_f(rough, 0.95, dust)

    rough = value(rough) if isinstance(rough, (int, float)) else rough
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
    return FinishNodes(
        mat, {"color": color, "roughness": rough, "metalness": metal}, bsdf, out
    )
