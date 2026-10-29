---
description: "LOD chain recipe in bpy: clean LOD0 first (merge 0.0001 m, dissolve degenerate, loose), ratios 1 / 0.5 / 0.25 / 0.1, screen sizes 0.5 / 0.25 / 0.125, SM_Name_LOD0..3 naming for Unreal, Unity and Godot"
metadata:
  label: "LOD Chain Recipe"
---

# LOD Chain Recipe

| LOD | Ratio of LOD0 tris | Screen size (UE) | Unity LODGroup % |
|---|---|---|---|
| LOD0 | 1.0 | 1.0 | 60 |
| LOD1 | 0.5 (40-60 %) | 0.5 | 30 |
| LOD2 | 0.25 (15-30 %) | 0.25 | 10 |
| LOD3 | 0.1 (5-10 %) | 0.125 | 2 (then cull) |

Clean LOD0 before decimating, or the doubles turn into holes at LOD2.

```python
import bpy, bmesh

def lod_chain(obj, ratios=(1, .5, .25, .1), base=None):
    base = base or obj.name
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=0.0001)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(obj.data); bm.free()
    obj.name = f"{base}_LOD0"
    for i, r in enumerate(ratios[1:], 1):
        lod = obj.copy(); lod.data = obj.data.copy(); lod.name = f"{base}_LOD{i}"
        obj.users_collection[0].objects.link(lod)
        m = lod.modifiers.new("lod", "DECIMATE"); m.ratio = r; m.use_symmetry = True
```

- Names: `SM_Crate_LOD0`, `SM_Crate_LOD1`… Unity builds a LODGroup from `_LODn`; Unreal imports them with "Import Mesh LODs" when they sit under one LOD group, otherwise generate LODs in UE from LOD0; Godot generates its own LODs, so export LOD0 only.
- UEFN: Nanite on opaque static meshes replaces LODs; ship LOD0.
- Check each level at its screen size in a `turntable-and-views` render; the silhouette must hold.

Adapted from Blender Agent Skills by EL4CTEO (optimization; MIT) and arjun988/blender-skills (LOD %, naming; MIT). Same chain as Forge `lods` + `export(lods=true)`.
