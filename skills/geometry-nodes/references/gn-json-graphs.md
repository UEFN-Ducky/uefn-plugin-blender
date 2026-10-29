# Geometry nodes as compact JSON

Write a graph as data, build it in one `blender_execute_blender_code` call, apply it, read back the tri count. Nodes are found by `bl_idname`, sockets by name; `in`/`out` are the group's Geometry sockets. Values are metres.

Rules for Blender 5.x: create the interface with `tree.interface.new_socket`; set modifier inputs by the socket **identifier** (`mod[item.identifier] = v`), never by display name; realize instances last; keep the `UVMap` attribute; finish with smooth by angle 30°.

```python
import bpy, math

def gn_build(spec, name="GN_Graph"):
    tree = bpy.data.node_groups.new(name, "GeometryNodeTree")
    tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    nodes = {"in": tree.nodes.new("NodeGroupInput"), "out": tree.nodes.new("NodeGroupOutput")}
    def sock(node, key, outputs):
        for s in (node.outputs if outputs else node.inputs):
            if s.enabled and key in (s.name, s.identifier):
                return s
        raise KeyError(f"{node.bl_idname} has no socket {key!r}")
    for n in spec["nodes"]:
        node = nodes[n["id"]] = tree.nodes.new(n["type"])
        for k, v in n.get("props", {}).items():
            setattr(node, k, v)
        for k, v in n.get("in", {}).items():
            sock(node, k, False).default_value = v
    for a, b in spec["links"]:
        (na, sa), (nb, sb) = a.split(".", 1), b.split(".", 1)
        tree.links.new(sock(nodes[na], sa, True), sock(nodes[nb], sb, False))
    return tree

def gn_apply(ob, spec):
    tree = gn_build(spec)
    mod = ob.modifiers.new("GN", "NODES"); mod.node_group = tree
    with bpy.context.temp_override(object=ob, active_object=ob):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.node_groups.remove(tree)
    me = ob.data
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    me.set_sharp_from_angle(angle=math.radians(30))
    return f"{len(me.polygons)} faces"

PEBBLES = {"nodes": [
    {"id": "pts", "type": "GeometryNodeDistributePointsOnFaces", "in": {"Density": 10.0}},
    {"id": "rock", "type": "GeometryNodeMeshIcoSphere", "in": {"Radius": 0.03, "Subdivisions": 1}},
    {"id": "inst", "type": "GeometryNodeInstanceOnPoints"},
    {"id": "real", "type": "GeometryNodeRealizeInstances"},
    {"id": "join", "type": "GeometryNodeJoinGeometry"}],
  "links": [["in.Geometry", "pts.Mesh"], ["pts.Points", "inst.Points"], ["rock.Mesh", "inst.Instance"],
            ["inst.Instances", "real.Geometry"], ["in.Geometry", "join.Geometry"], ["real.Geometry", "join.Geometry"],
            ["join.Geometry", "out.Geometry"]]}
WIRE = {"nodes": [
    {"id": "curve", "type": "GeometryNodeMeshToCurve"},
    {"id": "ring", "type": "GeometryNodeCurvePrimitiveCircle", "in": {"Radius": 0.01, "Resolution": 6}},
    {"id": "tube", "type": "GeometryNodeCurveToMesh", "in": {"Fill Caps": True}}],
  "links": [["in.Geometry", "curve.Mesh"], ["curve.Curve", "tube.Curve"], ["ring.Curve", "tube.Profile Curve"],
            ["tube.Mesh", "out.Geometry"]]}

bpy.ops.mesh.primitive_plane_add(size=2)
print(gn_apply(bpy.context.active_object, PEBBLES))
```

Budget: points × instance tris. `Density` is per m²: 10 on a 2 m plane = 40 pebbles of 20 tris.

## Scatter merged into one mesh (seeded, slope-limited)

When the engine needs one static mesh (UEFN, Roblox), copy items onto area-weighted random triangles instead of instancing. Same seed, same result.

```python
import bpy, bmesh, math, random
from mathutils import Matrix

def scatter_merge(on, items, density=20.0, seed=1, scale=(0.8, 1.2), max_slope=90, name="SM_Scatter"):
    rng = random.Random(seed); me = on.data; me.calc_loop_triangles(); mw = on.matrix_world
    tris = []
    for t in me.loop_triangles:
        a, b, c = (mw @ me.vertices[i].co for i in t.vertices); nor = (mw.to_3x3() @ t.normal).normalized()
        if nor.z >= math.cos(math.radians(max_slope)):
            tris.append((a, b, c, nor, (b - a).cross(c - a).length / 2))
    n = min(2000, round(sum(t[4] for t in tris) * density))
    bm = bmesh.new()
    for a, b, c, nor, _ in rng.choices(tris, weights=[t[4] for t in tris], k=n):
        u, v = rng.random(), rng.random()
        if u + v > 1: u, v = 1 - u, 1 - v
        it = rng.choice(items); tmp = it.data.copy()
        tmp.transform(Matrix.Translation(a + (b - a) * u + (c - a) * v) @ nor.to_track_quat("Z", "Y").to_matrix().to_4x4()
                      @ Matrix.Rotation(rng.uniform(0, 2 * math.pi), 4, "Z") @ Matrix.Scale(rng.uniform(*scale), 4))
        bm.from_mesh(tmp); bpy.data.meshes.remove(tmp)
    out = bpy.data.meshes.new(name); bm.to_mesh(out); bm.free()
    ob = bpy.data.objects.new(name, out); bpy.context.scene.collection.objects.link(ob)
    return f"{n} copies, {sum(len(p.vertices) - 2 for p in out.polygons)} tris"

bpy.ops.mesh.primitive_plane_add(size=4); ground = bpy.context.active_object
bpy.ops.mesh.primitive_ico_sphere_add(radius=0.1, subdivisions=1); pebble = bpy.context.active_object
print(scatter_merge(ground, [pebble], density=5, seed=3))
```

## Smooth organic union (SDF-style blend)

Join parts, voxel remesh, then smooth only the vertices near two or more source surfaces, so the seam gets a fillet and the rest stays crisp. Voxel ≈ 1 % of the size; fillet 2-4 voxels.

```python
import bpy, bmesh

def sdf_blend(objs, fillet=0.03, voxel=0.01, name="SM_Blend"):
    bm = bmesh.new()
    for o in objs:
        tmp = o.data.copy(); tmp.transform(o.matrix_world); bm.from_mesh(tmp); bpy.data.meshes.remove(tmp)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    out = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(out)
    me.remesh_voxel_size = voxel
    with bpy.context.temp_override(object=out, active_object=out):
        bpy.ops.object.voxel_remesh()
    def gap(o, co):
        ok, loc, _, _ = o.closest_point_on_mesh(o.matrix_world.inverted() @ co)
        return (o.matrix_world @ loc - co).length
    bm = bmesh.new(); bm.from_mesh(me)
    seam = [v for v in bm.verts if sorted(gap(o, v.co) for o in objs)[1] < fillet]
    for _ in range(max(2, round(fillet / voxel) * 2)):
        bmesh.ops.smooth_vert(bm, verts=seam, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bm.to_mesh(me); bm.free()
    for o in objs:
        o.hide_set(True)
    return f"{len(seam)} seam verts, {len(me.polygons)} faces"

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5); a = bpy.context.active_object
bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1.2, location=(0, 0, 0.6)); b = bpy.context.active_object
print(sdf_blend([a, b], fillet=0.08, voxel=0.03))
```

**Done when:** a render from front and 3/4 shows the scatter resting on the surface (none floating), the blend seam rounded with no step, and the printed counts fit the budget.

---
Adapted from Blender Agent Skills (geometry-nodes) by EL4CTEO, MIT licence. Same graphs as Forge `gn`, `scatter`, `sdf_blend`.
