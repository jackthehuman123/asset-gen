"""Abandoned Japanese village house exterior (ported from blueprint/spike/blender/house.py).
Runs inside Blender.

Coordinates: X along the front, Y depth (front at -Y), Z up. 1 unit = 1 stud.
The walls are centered on x/y; the ground is z=0.

Kawara roof: each tile column alternates a concave pan row (wide shallow arc, half-width
0.27, sagitta 0.08, open side up) and a convex cover row (narrow tall arc, half-width 0.13,
height 0.15) straddling the joint between two pans, 0.6 studs per pan+cover pair.
Tiles are laid in courses ~1.1 long down the slope; each tile rises toward its lower
end and ends in a lip, so it laps over the course below and course lines read across
the slope.
"""

import math
import random
from typing import Dict

import bmesh
import bpy
from mathutils import Matrix, Vector

from rbxasset.builders.house.roof_math import (
    COVER_H,
    COVER_HW,
    COVER_SEGS,
    EAVE_LIP,
    LIP,
    PAN_HW,
    PAN_SAG,
    PAN_SEGS,
    SLAB_T,
    STEP,
    TILE_BASE,
    TILE_LEN,
    TILE_PITCH,
    TILE_START,
    column_count,
    course_count,
)
from rbxasset.builders.result import BuildResult

TAGS = (
    "foundation",
    "frame",
    "siding",
    "plaster",
    "lattice",
    "doors",
    "boards",
    "engawa",
    "roof_base",
    "tiles_front",
    "tiles_back",
    "ridge",
    "eaves",
    "gable",
)


class Facade:
    """Local wall coords: u along the wall, v = world Z, w = outward normal."""

    def __init__(self, house, name, origin, U, Nrm, length):
        self.h = house
        self.name, self.O, self.U, self.N, self.L = (
            name,
            Vector(origin),
            Vector(U),
            Vector(Nrm),
            length,
        )

    def world(self, u, v, w):
        return self.O + self.U * u + Vector((0, 0, v)) + self.N * w

    def size(self, su, sv, sw):
        return Vector(
            (
                abs(self.U.x) * su + abs(self.N.x) * sw,
                abs(self.U.y) * su + abs(self.N.y) * sw,
                sv,
            )
        )

    def box(self, tag, u, v, w, su, sv, sw, tilt=0.0, bevel=0.0):
        o = self.h.wbox(tag, self.world(u, v, w), self.size(su, sv, sw), bevel=bevel)
        if tilt:
            o.rotation_mode = "AXIS_ANGLE"
            o.rotation_axis_angle = (tilt, self.N.x, self.N.y, self.N.z)
        return o


class _House:
    def __init__(self, p, rng):
        self.p, self.rng = p, rng
        self.parts = {k: [] for k in TAGS}
        self.W, self.D = p["width"], p["depth"]
        self.F, self.WH, self.WAIN = (
            p["floor_height"],
            p["wall_height"],
            p["wainscot_height"],
        )
        self.P = p["post_size"]
        self.PITCH = math.radians(p["roof_pitch_deg"])
        self.TOP = self.F + self.WH
        self.R = (self.D / 2) * math.tan(self.PITCH)
        self.ZR = self.TOP + self.R  # ridge line (top of wall plane extended)
        self.LX = self.W + 2 * p["gable_overhang"]

    def chance(self, key):
        return self.rng.random() < self.p.get(key, 0.0)

    # -------------------------------------------------------------- primitives
    def wbox(self, tag, center, size, rot=None, bevel=0.0):
        bpy.ops.mesh.primitive_cube_add(size=1, location=center)
        o = bpy.context.active_object
        o.scale = size
        if rot is not None:
            o.rotation_euler = rot
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        if bevel:
            mod = o.modifiers.new("Bevel", "BEVEL")
            mod.width, mod.segments, mod.limit_method = bevel, 1, "ANGLE"
        self.parts[tag].append(o)
        return o

    def mesh_obj(self, tag, name, verts, faces):
        me = bpy.data.meshes.new(name)
        me.from_pydata(verts, [], faces)
        me.update()
        o = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(o)
        self.parts[tag].append(o)
        return o

    def tile(self, tag, name, top, X, d, n, concave, eave):
        """One kawara tile. top: point on the profile axis at the tile's upper end.
        Pan (concave): a shallow dish, edges up; cover (convex): a narrow crown.
        The tile rises by STEP toward its lower end, which closes in a lip face
        (pans: a band; covers: a cap down past the chord). Only faces that can be
        seen are built: top surface + lip."""
        segs = PAN_SEGS if concave else COVER_SEGS
        hw = PAN_HW if concave else COVER_HW
        lip = EAVE_LIP if eave else LIP
        prof = []
        for i in range(segs + 1):
            if concave:
                u = -hw + 2 * hw * i / segs
                h = PAN_SAG * (u / hw) ** 2
            else:
                t = math.pi * i / segs
                u, h = -hw * math.cos(t), COVER_H * math.sin(t)
            prof.append((u, h))
        up = [top + X * u + n * h for u, h in prof]
        low_off = d * TILE_LEN + n * STEP
        low = [v + low_off for v in up]
        verts = up + low
        k = segs + 1
        faces = []

        def face(q, want):
            a, b, c = verts[q[0]], verts[q[1]], verts[q[2]]
            if (b - a).cross(c - a).dot(want) < 0:
                q = q[::-1]
            faces.append(q)

        for i in range(segs):  # top surface, facing up off the roof
            face([i, i + 1, k + i + 1, k + i], n)
        if concave:  # lip band hanging below the lower edge
            verts += [v - n * lip for v in low]
            for i in range(segs):
                face([k + i, k + i + 1, 2 * k + i + 1, 2 * k + i], d)
        else:  # cap: crown arc + its two ends dropped below the chord
            verts += [low[0] - n * lip, low[-1] - n * lip]
            face([2 * k] + list(range(k, 2 * k)) + [2 * k + 1], d)
        return self.mesh_obj(tag, name, [tuple(v) for v in verts], faces)

    # -------------------------------------------------------------- walls
    def siding(self, fc, u0, u1, v0, v1):
        rng = self.rng
        u = u0
        while u < u1 - 0.1:
            bw = min(0.45, u1 - u)
            if not self.chance("missing_boards"):
                top = v1
                if self.chance("broken_boards"):
                    top = v0 + (v1 - v0) * rng.uniform(0.3, 0.8)
                fc.box(
                    "siding",
                    u + bw / 2,
                    (v0 + top) / 2,
                    -0.05 + rng.uniform(-0.02, 0.02),
                    bw - 0.03,
                    top - v0,
                    0.12,
                    tilt=rng.uniform(-0.01, 0.01),
                )
            u += bw

    def plaster(self, fc, u0, u1, v0, v1):
        fc.box("plaster", (u0 + u1) / 2, (v0 + v1) / 2, -0.15, u1 - u0, v1 - v0, 0.25)

    def lattice(self, fc, u0, u1, v0, v1, w=0.0, tag="lattice", break_ok=True):
        rng = self.rng
        fr = 0.22
        fc.box(tag, (u0 + u1) / 2, v0 + fr / 2, w, u1 - u0, fr, 0.3)
        fc.box(tag, (u0 + u1) / 2, v1 - fr / 2, w, u1 - u0, fr, 0.3)
        fc.box(tag, u0 + fr / 2, (v0 + v1) / 2, w, fr, v1 - v0, 0.3)
        fc.box(tag, u1 - fr / 2, (v0 + v1) / 2, w, fr, v1 - v0, 0.3)
        n = max(2, int((u1 - u0 - 2 * fr) / 0.4))
        step = (u1 - u0 - 2 * fr) / n
        a, b = v0 + fr, v1 - fr
        for i in range(1, n):
            u = u0 + fr + i * step
            if break_ok and self.chance("broken_lattice"):
                if rng.random() < 0.4:
                    continue  # bar gone
                cut = a + (b - a) * rng.uniform(
                    0.2, 0.7
                )  # snapped: keep one end, angled
                if rng.random() < 0.5:
                    fc.box(
                        tag,
                        u,
                        (a + cut) / 2,
                        w,
                        0.14,
                        cut - a,
                        0.14,
                        tilt=rng.uniform(-0.15, 0.15),
                    )
                else:
                    fc.box(
                        tag,
                        u,
                        (cut + b) / 2,
                        w,
                        0.14,
                        b - cut,
                        0.14,
                        tilt=rng.uniform(-0.15, 0.15),
                    )
                continue
            fc.box(tag, u, (a + b) / 2, w, 0.14, b - a, 0.14)

    def door_panel(self, fc, u0, u1, v0, v1, w):
        fr = 0.25
        split = v0 + (v1 - v0) * 0.38
        fc.box(
            "doors", (u0 + u1) / 2, (v0 + split) / 2, w, u1 - u0 - 0.1, split - v0, 0.18
        )  # lower panel
        self.lattice(fc, u0, u1, split - fr, v1, w=w, tag="doors")

    def bay(self, fc, kind, idx, u0, u1):
        p, F, TOP = self.p, self.F, self.TOP
        boarded = [fc.name, idx] in [list(b) for b in p.get("boarded", [])]
        open_frac = next(
            (d[2] for d in p.get("door_open", []) if d[0] == fc.name and d[1] == idx),
            0.0,
        )
        if kind == "wall":
            self.siding(fc, u0, u1, F, F + self.WAIN)
            fc.box(
                "frame", (u0 + u1) / 2, F + self.WAIN, 0.0, u1 - u0, 0.35, 0.5
            )  # nuki rail
            self.plaster(fc, u0, u1, F + self.WAIN + 0.17, TOP - 0.6)
        elif kind == "window":
            s0, s1 = F + p["sill_height"], F + p["sill_height"] + p["window_height"]
            self.siding(fc, u0, u1, F, s0)
            fc.box("frame", (u0 + u1) / 2, s0, 0.0, u1 - u0, 0.3, 0.55)  # sill
            fc.box("frame", (u0 + u1) / 2, s1, 0.0, u1 - u0, 0.3, 0.55)  # head
            self.lattice(fc, u0, u1, s0 + 0.15, s1 - 0.15)
            self.plaster(fc, u0, u1, s1 + 0.15, TOP - 0.6)
            if boarded:
                for k in range(4):
                    v = s0 + 0.5 + k * (p["window_height"] - 1.0) / 3
                    fc.box(
                        "boards",
                        (u0 + u1) / 2,
                        v,
                        0.42,
                        u1 - u0 + 0.6,
                        0.55,
                        0.1,
                        tilt=self.rng.uniform(-0.12, 0.12),
                    )
        elif kind == "door":
            top = F + p["door_height"]
            fc.box("frame", (u0 + u1) / 2, top, 0.0, u1 - u0, 0.35, 0.55)  # lintel
            fc.box(
                "frame", (u0 + u1) / 2, F + 0.1, 0.0, u1 - u0, 0.2, 0.6
            )  # threshold rail
            self.plaster(fc, u0, u1, top + 0.17, TOP - 0.6)
            half = (u1 - u0) / 2
            # left panel fixed; right panel slid left by open_frac (behind the left one)
            self.door_panel(fc, u0, u0 + half, F + 0.2, top - 0.17, 0.05)
            shift = half * open_frac
            self.door_panel(
                fc, u0 + half - shift, u1 - shift, F + 0.2, top - 0.17, -0.2
            )

    def build_facade(self, fc, bays):
        P, F, WH, TOP = self.P, self.F, self.WH, self.TOP
        bw = fc.L / len(bays)
        for i in range(len(bays)):  # posts (corner post at i=0 belongs to this facade)
            fc.box("frame", -fc.L / 2 + i * bw, F + WH / 2, 0.0, P, WH, P, bevel=0.03)
        fc.box("frame", 0, TOP - 0.3, 0.05, fc.L + P, 0.6, 0.7, bevel=0.03)  # top plate
        fc.box("frame", 0, F + 0.15, 0.05, fc.L + P, 0.3, 0.6)  # sill plate
        for i, kind in enumerate(bays):
            u0 = -fc.L / 2 + i * bw + P / 2
            u1 = -fc.L / 2 + (i + 1) * bw - P / 2
            self.bay(fc, kind, i, u0, u1)

    # -------------------------------------------------------------- base, floor, engawa
    def base(self):
        W, D, F = self.W, self.D, self.F
        self.wbox("foundation", (0, 0, (F - 0.2) / 2), (W + 0.4, D + 0.4, F - 0.2))
        self.wbox("engawa", (0, 0, F - 0.1), (W - 0.2, D - 0.2, 0.2))  # interior floor
        y_out = -D / 2 - self.p["engawa_depth"]
        y = -D / 2 - 0.3
        while y > y_out + 0.25:
            if not self.chance("missing_engawa_planks"):
                self.wbox("engawa", (0, y, F - 0.12), (W + 0.6, 0.46, 0.18), bevel=0.02)
            y -= 0.5
        self.wbox(
            "engawa", (0, y_out + 0.15, F - 0.35), (W + 0.6, 0.3, 0.4)
        )  # edge beam
        x = -W / 2
        while x <= W / 2 + 0.01:
            self.wbox(
                "engawa", (x, y_out + 0.4, (F - 0.4) / 2 + 0.3), (0.45, 0.45, F - 0.7)
            )
            self.wbox("foundation", (x, y_out + 0.4, 0.15), (0.9, 0.9, 0.3), bevel=0.05)
            x += W / 6
        door_x = -W / 2 + 2.5 * (W / len(self.p["facades"]["front"]))
        self.wbox(
            "foundation", (door_x, y_out - 0.6, 0.25), (2.6, 1.2, 0.5), bevel=0.08
        )  # step stone

    # -------------------------------------------------------------- gable ends
    def gable(self, fc, x_sign):
        D, TOP, ZR, R = self.D, self.TOP, self.ZR, self.R
        x = x_sign * self.W / 2
        t = 0.3
        verts = []
        for dx in (-t / 2, t / 2):
            verts += [
                (x + dx, -D / 2, TOP),
                (x + dx, D / 2, TOP),
                (x + dx, 0, ZR - 0.2),
            ]
        faces = [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
        o = self.mesh_obj("gable", "gable", verts, faces)
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(o.data)
        bm.free()
        fc.box("frame", 0, TOP + 0.3, 0.25, D, 0.5, 0.4)  # tie beam
        fc.box("frame", 0, TOP + R / 2, 0.25, 0.5, R, 0.4)  # king post
        for s in (-1, 1):  # struts
            fc.box("frame", s * D / 4, TOP + R / 4, 0.25, 0.35, R / 2, 0.35)

    # -------------------------------------------------------------- roof
    def tile_column(self, tag, name, ridge, d, n, slab_l, x, concave):
        """One column of tile courses down the slope; the eave tile is capped.
        Courses are evenly spaced so the last one hangs just past the slab edge."""
        rng = self.rng
        s0, s_end = TILE_START, slab_l + 0.1
        ncourse = course_count(slab_l)
        step = (s_end - s0 - TILE_LEN) / max(1, ncourse - 1)
        X0 = Vector((1, 0, 0))
        base = SLAB_T / 2 + TILE_BASE + (0.0 if concave else PAN_SAG * 0.3)
        for k in range(ncourse):
            if self.chance("missing_tiles"):
                continue
            s = s0 + k * step
            lift = 0.0
            # tiny per-tile jitter so the rows aren't machine-perfect
            yaw = rng.uniform(-0.012, 0.012)
            off = rng.uniform(-0.01, 0.01)
            if self.chance("slipped_tiles"):
                s += rng.uniform(0.25, 0.6)
                lift = 0.05
                yaw += rng.uniform(-0.08, 0.08)
            R = Matrix.Rotation(yaw, 3, n)
            X, dd = R @ X0, R @ d
            top = ridge + d * s + n * (base + lift) + X0 * (x + off)
            self.tile(
                tag, "%s_%d" % (name, k), top, X, dd, n, concave, k == ncourse - 1
            )

    def roof(self):
        p, LX, PITCH, ZR = self.p, self.LX, self.PITCH, self.ZR
        run = self.D / 2 + p["eave_overhang"]
        slab_l = run / math.cos(PITCH)
        roof_objs = []
        for side, tiles_tag in ((-1, "tiles_front"), (1, "tiles_back")):
            d = Vector((0, side * math.cos(PITCH), -math.sin(PITCH)))  # down-slope
            n = Vector((1, 0, 0)).cross(d)
            if n.z < 0:
                n = -n
            ridge = Vector((0, 0, ZR))
            rot = (-side * PITCH, 0, 0)
            mid = ridge + d * (slab_l / 2)
            roof_objs.append(self.wbox("roof_base", mid, (LX, slab_l, SLAB_T), rot=rot))
            first = len(self.parts[tiles_tag])
            ncols = column_count(LX)
            for c in range(ncols):
                xp = -LX / 2 + TILE_PITCH / 2 + c * TILE_PITCH
                self.tile_column(
                    tiles_tag,
                    "pan_%s_%02d" % (tiles_tag[6:], c),
                    ridge,
                    d,
                    n,
                    slab_l,
                    xp,
                    concave=True,
                )
                if c < ncols - 1:  # cover over the joint between this pan and the next
                    self.tile_column(
                        tiles_tag,
                        "cover_%s_%02d" % (tiles_tag[6:], c),
                        ridge,
                        d,
                        n,
                        slab_l,
                        xp + TILE_PITCH / 2,
                        concave=False,
                    )
            roof_objs += self.parts[tiles_tag][first:]
            # fascia along the eave + rafter ends under the eave
            eave_pt = ridge + d * slab_l
            roof_objs.append(
                self.wbox("eaves", eave_pt - n * 0.35, (LX, 0.15, 0.6), rot=rot)
            )
            xr = -LX / 2 + 0.6
            while xr < LX / 2 - 0.3:
                c = ridge + d * (slab_l - 1.0) - n * 0.38 + Vector((xr, 0, 0))
                roof_objs.append(self.wbox("eaves", c, (0.28, 2.0, 0.32), rot=rot))
                xr += 1.2
            for gx in (-1, 1):  # barge boards at the gable overhang
                c = mid + Vector((gx * (LX / 2 - 0.1), 0, 0)) - n * 0.3
                roof_objs.append(self.wbox("eaves", c, (0.2, slab_l, 0.6), rot=rot))

        roof_objs.append(
            self.wbox("ridge", (0, 0, ZR + 0.45), (LX + 0.2, 0.9, 0.7), bevel=0.05)
        )
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=12,
            radius=0.38,
            depth=LX + 0.4,
            location=(0, 0, ZR + 0.85),
            rotation=(0, math.pi / 2, 0),
        )
        self.parts["ridge"].append(bpy.context.active_object)
        roof_objs.append(bpy.context.active_object)
        for gx in (-1, 1):  # onigawara end blocks
            roof_objs.append(
                self.wbox(
                    "ridge",
                    (gx * (LX / 2 + 0.15), 0, ZR + 0.9),
                    (0.45, 1.6, 1.7),
                    bevel=0.08,
                )
            )
        if p.get("roof_sag", 0.0):
            self.sag(roof_objs, p["roof_sag"])

    def sag(self, objs, sag):
        """Bake transforms, cut long pieces along X so they can bend, then drop
        vertices toward the middle of the ridge."""
        LX, TOP, ZR = self.LX, self.TOP, self.ZR
        for o in objs:
            if o.matrix_basis != Matrix.Identity(4):
                o.data.transform(o.matrix_basis)
                o.matrix_basis = Matrix.Identity(4)
            xs = [vv.co.x for vv in o.data.vertices]
            if max(xs) - min(xs) > 3:
                bm = bmesh.new()
                bm.from_mesh(o.data)
                x = min(xs) + 1.5
                while x < max(xs) - 0.1:
                    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
                    bmesh.ops.bisect_plane(
                        bm, geom=geom, plane_co=(x, 0, 0), plane_no=(1, 0, 0)
                    )
                    x += 1.5
                bm.to_mesh(o.data)
                bm.free()
            for vtx in o.data.vertices:
                t = max(0.0, 1 - (2 * vtx.co.x / LX) ** 2)
                height = max(0.0, min(1.0, (vtx.co.z - TOP + 1.5) / (ZR - TOP + 1.5)))
                vtx.co.z -= sag * t * (0.4 + 0.6 * height)
            o.data.update()

    # -------------------------------------------------------------- shots
    def shots(self, facades):
        p, W, D, F, ZR = self.p, self.W, self.D, self.F, self.ZR
        k = max(W / 28.0, D / 20.0, ZR / 17.4)  # spike framing was tuned for 28 x 20
        # close-up on the (first) half-open door, else the first front door/window bay
        side, idx = "front", None
        if p.get("door_open"):
            side, idx = p["door_open"][0][0], p["door_open"][0][1]
        else:
            bays = p["facades"]["front"]
            idx = next((i for i, b in enumerate(bays) if b != "wall"), len(bays) // 2)
        fc = facades[side]
        bays = p["facades"][side]
        u = -fc.L / 2 + (idx + 0.5) * fc.L / len(bays)
        tgt = fc.world(u, F + p["door_height"] * 0.45, 0)
        cam = fc.world(u - 2.5, 4.5, 11)
        return [
            ("wide", (-30 * k, -42 * k, 14 * k), (0.0, 0.0, 7 * k), 35.0),
            ("front", (2 * k, -30 * k, 5.5 * k), (2 * k, 0.0, 7 * k), 40.0),
            ("close_opening", tuple(cam), tuple(tgt), 45.0),
            ("roof", (24 * k, -22 * k, 26 * k), (2 * k, 0.0, 13 * k), 40.0),
        ]

    def build(self):
        W, D = self.W, self.D
        facades = {
            "front": Facade(self, "front", (0, -D / 2, 0), (1, 0, 0), (0, -1, 0), W),
            "back": Facade(self, "back", (0, D / 2, 0), (-1, 0, 0), (0, 1, 0), W),
            "left": Facade(self, "left", (-W / 2, 0, 0), (0, 1, 0), (-1, 0, 0), D),
            "right": Facade(self, "right", (W / 2, 0, 0), (0, -1, 0), (1, 0, 0), D),
        }
        for name, fc in facades.items():
            self.build_facade(fc, self.p["facades"][name])
        self.base()
        self.gable(facades["left"], -1)
        self.gable(facades["right"], 1)
        self.roof()
        return BuildResult(self.parts, self.shots(facades), {"W": W, "H": self.ZR})


def build(params: Dict, rng: random.Random) -> BuildResult:
    return _House(params, rng).build()
