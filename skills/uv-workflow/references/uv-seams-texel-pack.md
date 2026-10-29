---
description: "bpy UV recipe: seams on edges sharper than 60°, unwrap (angle-based or minimum stretch), average island scale, scale to a texel target in px/m, pack with margin res/256 (1k 4, 2k 8, 4k 16 px), a lightmap UV2 with 0.02 margin, mirrored +1 U, and a report of islands, overlap %, texel and spread"
metadata:
  label: "UV Seams, Texel, Pack"
---

# UV Seams, Texel, Pack

| Tier | Texel (px/m) |
|---|---|
| mobile / background | 256 |
| third-person game prop | 512 |
| hero, first-person | 1024 |

Pack margin = res / 256 px: 1k → 4, 2k → 8, 4k → 16. Spread (densest / sparsest island) ≤ 1.3. Pack efficiency > 75 % on unique UVs.

```python
import bpy, math, numpy as np

def area_ratio(ob):
    me = ob.data; uv = me.uv_layers.active.data; mw = ob.matrix_world
    a2 = a3 = 0.0
    for p in me.polygons:
        l = list(p.loop_indices); v = [mw @ me.vertices[me.loops[i].vertex_index].co for i in l]
        u = [uv[i].uv for i in l]
        for k in range(1, len(l) - 1):
            a3 += ((v[k] - v[0]).cross(v[k + 1] - v[0])).length / 2
            a2 += abs((u[k] - u[0]).cross(u[k + 1] - u[0])) / 2
    return math.sqrt(a2 / a3)          # UV units per metre

def unwrap(ob, texel=512, res=2048, angle=60, method="ANGLE_BASED", lightmap=False):
    bpy.context.view_layer.objects.active = ob
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.mesh.edges_select_sharp(sharpness=math.radians(angle)); bpy.ops.mesh.mark_seam(clear=False)
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.unwrap(method=method, margin=0)   # or "MINIMUM_STRETCH" for curved panels
    bpy.ops.uv.average_islands_scale()
    bpy.ops.object.mode_set(mode="OBJECT")
    if texel:                                    # scale every island to the target density
        f = texel / (area_ratio(ob) * res)
        uv = ob.data.uv_layers.active.data
        for d in uv: d.uv *= f
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(rotate=True, scale=not texel, margin_method="FRACTION", margin=max(2, res // 256) / res)
    bpy.ops.object.mode_set(mode="OBJECT")
```

- A closed smooth part (sphere, capsule) has no sharp edge: mark one seam by hand or use `bpy.ops.uv.smart_project(angle_limit=math.radians(66))`.
- Islands past 0-1 after `scale=False` mean the texel does not fit `res`: raise res or lower texel.
- **Lightmap UV2:** `me.uv_layers.new(name="UVMap_Lightmap")`, make it active, `bpy.ops.uv.smart_project(island_margin=0.02)` or Lightmap Pack (margin 0.02+), no overlaps, all in 0-1; set UVMap back active for render. UE: Source Lightmap Index 0, Destination 1 if you do not ship UV2.
- **Mirrored halves:** stack them for texture space, then offset one half +1 U before a bake so the baker sees one copy; never overlap on a lightmap.

## Report

Islands: `bpy_extras.mesh_utils.mesh_linked_uv_islands(me)`. Overlap: rasterise the UV triangles into a 512² grid with an island id per pixel; pixels claimed by two islands / covered pixels. Texel = `area_ratio(ob) * res`. Spread = max / min of the per-island ratio (ignore islands under 0.2 % of the area).

Done when: 0 % overlap (mirrors excepted), texel within 10 % of target, spread ≤ 1.3, all islands in 0-1.

Adapted from Blender Agent Skills by EL4CTEO (retopology-uv; MIT). Same recipe as Forge `uv(method, texel, res, margin_px, lightmap, check)`.
