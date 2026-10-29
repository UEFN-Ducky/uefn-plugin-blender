# Headless sculpt chain

Sculpt mode brushes need a viewport. Over MCP, shape the mesh with a chain of bmesh / modifier steps instead, in one `blender_execute_blender_code` call, and look after each pass.

| Step | Does | Typical |
|---|---|---|
| `remesh` | voxel remesh: even, watertight | 1 % of height (0.02 m on a 2 m figure) |
| `inflate` | move along normals (negative thins) | 0.5-2 % of size |
| `smooth` | relax n passes, factor 0.5 | 1-3 |
| `symmetrize` | copy +X half onto -X (`X`, `-X`, `Y`...) | after primary |
| `detail` | fractal noise along normals | strength 1 %, scale 15 % of size |
| `multires` | Catmull-Clark subdivide n, applied | cap 400k faces |

Passes: **primary** (mass, silhouette: remesh, inflate, symmetrize) → **secondary** (planes, forms: large-scale detail, smooth) → **tertiary** (surface: small-scale detail, or a multires sidecar baked to a normal map). Remesh before UVs and rigging, never after.

```python
import bpy, bmesh, random
from mathutils import Vector, noise

def sculpt_chain(ob, steps):
    def bm_do(fn):
        bm = bmesh.new(); bm.from_mesh(ob.data); bm.normal_update(); fn(bm); bm.to_mesh(ob.data); bm.free(); ob.data.update()
    ctx = bpy.context.temp_override(object=ob, active_object=ob)
    for name, v in steps:
        if name == "remesh":
            ob.data.remesh_voxel_size = v
            with ctx: bpy.ops.object.voxel_remesh()
        elif name == "inflate":
            bm_do(lambda bm: [setattr(x, "co", x.co + x.normal * v) for x in bm.verts])
        elif name == "smooth":
            bm_do(lambda bm: [bmesh.ops.smooth_vert(bm, verts=bm.verts[:], factor=.5, use_axis_x=True, use_axis_y=True, use_axis_z=True) for _ in range(v)])
        elif name == "symmetrize":
            bm_do(lambda bm: bmesh.ops.symmetrize(bm, input=bm.verts[:] + bm.edges[:] + bm.faces[:], direction=v, dist=1e-4 * max(ob.dimensions)))
        elif name == "detail":
            k, scale, seed = v
            off = Vector([random.Random(seed).uniform(-100, 100) for _ in range(3)])
            bm_do(lambda bm: [setattr(x, "co", x.co + x.normal * k * noise.fractal(x.co / scale + off, 1.0, 2.0, 4)) for x in list(bm.verts)])
        elif name == "multires":
            assert len(ob.data.polygons) * 4 ** v <= 400000, "too dense: use a multires sidecar"
            m = ob.modifiers.new("sub", "SUBSURF"); m.levels = m.render_levels = v
            with ctx: bpy.ops.object.modifier_apply(modifier=m.name)
    return f"{len(steps)} steps, {sum(len(p.vertices) - 2 for p in ob.data.polygons)} tris"

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.4)
rock = bpy.context.active_object
print(sculpt_chain(rock, [("remesh", 0.02), ("detail", (0.06, 0.3, 3)), ("symmetrize", "X"), ("smooth", 2), ("detail", (0.01, 0.06, 7))]))
```

Note: `detail` reads `x.co` while moving it, which is fine for noise; for exact displacement collect the moves first.

**Done when:** front and side renders show the intended mass from both views, the two halves match after `symmetrize`, and tris fit the budget (game rock 0.5-3k after decimate/retopo).

---
Adapted from Blender Agent Skills (sculpting) by EL4CTEO, MIT licence. Same steps as Forge `sculpt(ops=[...])`.
