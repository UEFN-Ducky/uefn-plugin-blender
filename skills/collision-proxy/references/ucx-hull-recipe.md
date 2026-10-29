---
description: "Convex UCX hulls in bpy: hull of up to 32 extreme points shrunk 2 percent, one hull per convex part, UCX_<Mesh>_01 naming, Godot -colonly and Unity MeshCollider equivalents"
metadata:
  label: "UCX Hull Recipe"
---

# UCX Hull Recipe

- One convex hull per convex part: a table is top + 4 legs = 5 hulls, never one hull over the whole table.
- Max 32 verts per hull (UE caps convex hulls; fewer is faster). Shrink 0.98 about the centre so it never pokes out of the render mesh.
- Name `UCX_<RenderMeshName>_01`, `_02`… The render mesh name must match exactly (`UCX_SM_Table_01` for `SM_Table`). Same origin as the render mesh.

```python
import bpy, bmesh, math
from mathutils import Vector

def ucx(obj, index=1, max_verts=32, shrink=0.98):
    pts = [obj.matrix_world @ v.co for v in obj.data.vertices]
    g = math.pi * (3 - math.sqrt(5)); keep = []
    for i in range(max_verts):  # extreme point along each Fibonacci-sphere direction
        z = 1 - 2 * (i + .5) / max_verts; r = math.sqrt(1 - z * z)
        d = Vector((r * math.cos(g * i), r * math.sin(g * i), z))
        p = max(pts, key=d.dot)
        if all((p - q).length > 1e-6 for q in keep): keep.append(p)
    c = sum(keep, Vector()) / len(keep)
    bm = bmesh.new()
    for p in keep: bm.verts.new(c + (p - c) * shrink)
    bmesh.ops.convex_hull(bm, input=bm.verts)
    me = bpy.data.meshes.new(f"UCX_{obj.name}_{index:02d}"); bm.to_mesh(me); bm.free()
    hull = bpy.data.objects.new(me.name, me); obj.users_collection[0].objects.link(hull)
    hull.display_type = "WIRE"
    return hull
```

The hull is built in world space; export it with the render mesh selected, before applying any other transform.

| Engine | What to ship |
|---|---|
| Unreal / UEFN FBX | `UCX_<Mesh>_##` in the same FBX |
| Godot GLB | rename to `<Mesh>_01-colonly` (invisible static collider) or suffix the render mesh `-col` |
| Unity | leave hulls out; add MeshCollider (Convex) on the prefab |
| Roblox | leave hulls out; set CollisionFidelity = Hull / Box on the MeshPart |

Adapted from arjun988/blender-skills (collision UCX_; MIT) and Blender Agent Skills by EL4CTEO (export-pipelines; MIT). Same output as Forge `collision`.
