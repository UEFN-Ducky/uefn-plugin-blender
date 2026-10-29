# Booleans with cleanup and detail kits

## Applied boolean + cleanup

Cutters live in a hidden `COL_Booleans` collection and pass **through** the surface by a few cm on both sides (a grazing cutter leaves skins). Exact solver for mechanical work; `MANIFOLD` is faster on closed meshes.

```python
import bpy, bmesh

def bool_apply(ob, cutter, op="DIFFERENCE", solver="EXACT"):
    m = ob.modifiers.new("HS_Bool", "BOOLEAN")
    m.operation, m.solver, m.object = op, solver, cutter
    if solver == "EXACT":
        m.use_self = True  # a joined cutter may overlap itself
    with bpy.context.temp_override(object=ob, active_object=ob):
        bpy.ops.object.modifier_apply(modifier=m.name)
    bm = bmesh.new(); bm.from_mesh(ob.data)  # no Merge by Distance here: it opens edges on stacked exact cuts
    bmesh.ops.dissolve_degenerate(bm, dist=1e-7, edges=bm.edges[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    open_edges = sum(1 for e in bm.edges if len(e.link_faces) != 2)
    bm.to_mesh(ob.data); bm.free()
    col = bpy.data.collections.get("COL_Booleans") or bpy.data.collections.new("COL_Booleans")
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    for c in list(cutter.users_collection):
        c.objects.unlink(cutter)
    col.objects.link(cutter); cutter.hide_set(True); cutter.hide_render = True
    return f"{op.lower()}: {len(ob.data.polygons)} faces, open edges {open_edges}"
```

## Detail kits along a surface normal

Panel grooves, vent slots, grille holes and bolts, built as one cutter aligned to the surface nearest `at` (world metres), then one boolean.

| kit | Parts | Op |
|---|---|---|
| `panel` | n x n panels: (n+1) grooves each way, groove = max(depth, 1.5 % of size) | difference |
| `vent` | n slots, slot height = half the pitch | difference |
| `grille` | n x n holes, radius 0.3 x pitch, 12 seg | difference |
| `bolt` | n heads on a ring of `size`, radius 5 % of size, 8 seg, stand `depth` proud | union |

```python
import bpy, bmesh, math
from mathutils import Matrix, Vector

def detail_kit(ob, kit="panel", at=None, size=None, depth=None, n=None):
    span = max(ob.dimensions); size = size or span * 0.3; depth = depth or span * 0.01
    n = n or {"panel": 2, "vent": 5, "grille": 4, "bolt": 4}[kit]
    mw = ob.matrix_world
    at = Vector(at) if at else mw @ Vector((0, 0, max(v.co.z for v in ob.data.vertices) + 1))
    ok, loc, nor, _ = ob.closest_point_on_mesh(mw.inverted() @ at)
    frame = Matrix.Translation(mw @ loc) @ (mw.to_3x3() @ nor).normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
    h, parts = 2 * depth, []
    if kit == "panel":
        g = max(depth, size * 0.015); lines = [-size / 2 + i * size / n for i in range(n + 1)]
        parts = [("box", (size + g, g, h), (0, y, 0)) for y in lines] + [("box", (g, size + g, h), (x, 0, 0)) for x in lines]
    elif kit == "vent":
        s = size / n; parts = [("box", (size, s / 2, h), (0, -size / 2 + s * (i + .5), 0)) for i in range(n)]
    elif kit == "grille":
        s = size / n; parts = [("cyl", (0.6 * s, 0.6 * s, h), (-size / 2 + s * (i + .5), -size / 2 + s * (j + .5), 0)) for i in range(n) for j in range(n)]
    else:
        r = size * 0.05; parts = [("cyl", (2 * r, 2 * r, h), (size / 2 * math.cos(a), size / 2 * math.sin(a), 0)) for a in (2 * math.pi * (i + .5) / n for i in range(n))]
    bm = bmesh.new()
    for shape, dims, off in parts:
        m = frame @ Matrix.Translation(off) @ Matrix.Diagonal((*dims, 1))
        if shape == "box":
            bmesh.ops.create_cube(bm, size=1, matrix=m)
        else:
            bmesh.ops.create_cone(bm, cap_ends=True, segments=8 if kit == "bolt" else 12, radius1=.5, radius2=.5, depth=1, matrix=m)
    me = bpy.data.meshes.new("SM_Cutter_" + kit); bm.to_mesh(me); bm.free()
    cutter = bpy.data.objects.new(me.name, me); bpy.context.scene.collection.objects.link(cutter)
    return bool_apply(ob, cutter, "UNION" if kit == "bolt" else "DIFFERENCE")

bpy.ops.mesh.primitive_cube_add(size=1)
crate = bpy.context.active_object
print(detail_kit(crate, "panel", at=(0, -1, 0), size=0.7, depth=0.006))
print(detail_kit(crate, "bolt", at=(0, -1, 0), size=0.8, depth=0.01))
```

**Done when:** `open edges 0` on every call and a front render shows even grooves and evenly spaced bolt heads; then add `hs_stack(ob, "midpoly")` from [midpoly-stack](midpoly-stack.md).

| Symptom | Fix |
|---|---|
| open edges > 0 | cutter grazes a face: lengthen it or move `at` |
| streaky shading | Weighted Normal (midpoly stack) |
| kit on the wrong face | put `at` just outside the face you want |

---
Adapted from Blender Agent Skills (hardsurface-modeling) by EL4CTEO, MIT licence. Same kits as Forge `hardsurface(preset=...)`.
