---
description: "Pick the retopo method (QuadriFlow for organics after a voxel remesh, Decimate to keep UVs, Planar / limited dissolve for hard surface) with bpy calls, edge-flow numbers (3 loops per joint, 3+ rings at eyes and mouth, poles off bends) and a bmesh topology report: quads %, tris, ngons, poles"
metadata:
  label: "Retopo Methods and Report"
---

# Retopo Methods and Report

| Mesh | Method | bpy |
|---|---|---|
| sculpt, scan, organic | voxel remesh at ~1 % of height, then QuadriFlow; re-UV after | `ob.data.remesh_voxel_size = h * 0.01; bpy.ops.object.voxel_remesh()`; `bpy.ops.object.quadriflow_remesh(target_faces=4000, use_mesh_symmetry=True, use_preserve_sharp=True)` |
| AI / heavy mesh whose UVs you keep, LODs | Decimate (collapse) | `m = ob.modifiers.new("dec", "DECIMATE"); m.ratio = 0.25; m.use_symmetry = True` |
| hard surface | planar dissolve, then clean by hand | `m.decimate_type = "DISSOLVE"; m.angle_limit = math.radians(5)` |
| hero character | shrinkwrap manual retopo | see SKILL.md shrinkwrap setup |

Edge flow for anything that bends:
- 3 edge loops at each joint (elbow, knee, knuckle, jaw); 3+ rings round eyes and mouth.
- Poles (3 or 5+ edges) on flat spans: chest, back of head, under the arm. Never on the bend line.
- Even quads where it deforms; triangles only on flat, hidden, non-deforming spots.
- Density follows deformation: face and hands get ~2× the body's edge density.

```python
import bmesh

def topology(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    sizes = [len(f.verts) for f in bm.faces]
    inner = [v for v in bm.verts if not v.is_boundary]
    poles = [v for v in inner if len(v.link_edges) != 4]
    r = {"faces": len(sizes), "quads_pct": round(100 * sizes.count(4) / max(1, len(sizes)), 1),
         "tris": sizes.count(3), "ngons": sum(s > 4 for s in sizes),
         "poles": len(poles), "poles_pct": round(100 * len(poles) / max(1, len(inner)), 1)}
    bm.free(); return r
```

Done when: ngons 0 on deforming meshes, quads ≥ 90 %, poles off every joint (select them: `v.select = True` for `poles`, then look), silhouette matches the high-poly. Then UVs: `uv-workflow` → `uv-seams-texel-pack`.

Adapted from Blender Agent Skills by EL4CTEO (retopology-uv; MIT). Same report as Forge `topology`.
