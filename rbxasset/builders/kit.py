"""Shared bpy primitives for builders. Runs inside Blender. Units: studs."""
import bmesh
import bpy
import mathutils


class Kit:
    def __init__(self, tags):
        self.parts = {t: [] for t in tags}

    def _add(self, tag, obj):
        self.parts[tag].append(obj)
        return obj

    def box(self, tag, size, loc, rot=(0, 0, 0), bevel=0.01):
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
        o = bpy.context.active_object
        o.scale = size
        bpy.ops.object.transform_apply(scale=True)
        if bevel:
            m = o.modifiers.new("Bevel", "BEVEL")
            m.width, m.segments, m.limit_method = bevel, 1, "ANGLE"
        return self._add(tag, o)

    def cyl(self, tag, r, depth, loc, rot=(0, 0, 0), verts=16):
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
        return self._add(tag, bpy.context.active_object)

    def cone(self, tag, r1, r2, depth, loc, rot=(0, 0, 0), verts=16):
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=depth,
                                        location=loc, rotation=rot)
        return self._add(tag, bpy.context.active_object)

    def sphere(self, tag, r, loc, scale=(1, 1, 1)):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=r, location=loc)
        o = bpy.context.active_object
        o.scale = scale
        bpy.ops.object.transform_apply(scale=True)
        return self._add(tag, o)

    def revolve(self, tag, profile, segments=24, loc=(0, 0, 0), closed=False):
        """Spin a (radius, z) profile around the z axis into a solid of revolution.
        closed=True joins the last profile point back to the first (ring solids)."""
        bm = bmesh.new()
        vs = [bm.verts.new((r, 0.0, z)) for r, z in profile]
        es = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
        if closed:
            es.append(bm.edges.new((vs[-1], vs[0])))
        bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(0, 0, 1), angle=6.283185307,
                       steps=segments, use_merge=True)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        mesh = bpy.data.meshes.new(tag)
        bm.to_mesh(mesh)
        bm.free()
        for poly in mesh.polygons:
            poly.use_smooth = True
        o = bpy.data.objects.new(tag, mesh)
        o.location = loc
        bpy.context.scene.collection.objects.link(o)
        return self._add(tag, o)

    def mesh(self, tag, verts, faces):
        """A closed solid from raw verts and polygon faces (normals recalculated)."""
        me = bpy.data.meshes.new(tag)
        me.from_pydata(verts, [], faces)
        me.update()
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(tag, me)
        bpy.context.scene.collection.objects.link(o)
        return self._add(tag, o)

    def prism(self, tag, profile, x0, x1):
        """Extrude a (y, z) polygon along x from x0 to x1."""
        n = len(profile)
        verts = [(x0, y, z) for y, z in profile] + [(x1, y, z) for y, z in profile]
        faces = [list(range(n)), list(range(2 * n - 1, n - 1, -1))]
        faces += [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
        return self.mesh(tag, verts, faces)

    @staticmethod
    def rotate_z(objs, angle):
        """Rotate objects about the world z axis through the origin."""
        rz = mathutils.Matrix.Rotation(angle, 4, "Z")
        for o in objs:
            o.matrix_world = rz @ o.matrix_world
