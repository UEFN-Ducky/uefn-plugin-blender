---
description: "FPS vs TPS weapon budgets: triangles, materials, texture size and texel density, LOD ratios and screen sizes, viewmodel FOV, collision"
metadata:
  label: "Weapon budgets FPS vs TPS"
---

# Weapon budgets: FPS vs TPS

| use | tris (LOD0) | materials | textures | texel density |
|---|---|---|---|---|
| FPS hero viewmodel | 8-20k (AAA 30-60k) | 2-3 | 2048-4096 per sheet | 20-40 px/cm |
| TPS / character-held | 3-6k | 1-3 | 1024-2048 | 8-12 px/cm |
| world pickup / display | 1-3k | 1 (atlas) | 512-1024 | 5 px/cm |
| mobile | 1-3k | 1 | 512-1024 | 5 px/cm |

LODs (same silhouette, drop the inner detail first):

| LOD | tris | UE screen size |
|---|---|---|
| 0 | 100 % | 1.0 |
| 1 | 50 % | 0.5 |
| 2 | 25 % | 0.25 |
| 3 | 10 % | 0.1 |

FPS rules: the viewmodel renders at FOV 55-70 (world 90), so the rear (sights, receiver top, charging handle) gets the detail and the polygons; the muzzle end is small on screen. Hide the inside of the mag well and the barrel bore beyond 2-3 cm. TPS rules: the silhouette at 3-5 m is all that reads; merge to one mesh, details into the normal map.

Collision: a box or 2-3 convex hulls (`UCX_<Mesh>_00`) for pickups; held weapons usually need none.

Export checks: scale applied, triangulated (or let the engine), one UV channel for textures + one for lightmap on world props, material slots named for the engine, sockets per `../../hard-surface/references/weapons-modular.md`.

```python
import bpy
ob = bpy.context.active_object
tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
print(ob.name, tris, "tris,", len(ob.material_slots), "materials")  # compare with the table
```

Done when: tris and material count fit the row for the weapon's camera, and LOD1-3 keep the side silhouette in a render.

Forge path: `weapon` meshes come out at 0.3-6k tris (TPS-ready); check with `{"tool": "forge_hq", "op": "qa", "params": {"id": "$0", "budget": "weapon"}}`.

---
Budget and LOD tables adapted from Blender Agent Skills (optimization) by EL4CTEO, MIT licence.
