---
description: "Triangle, material and texture budgets per asset class and platform (UEFN, Unreal, Roblox, web, mobile) and the reduction order that keeps the silhouette"
metadata:
  label: "Budgets by Class"
---

# Budgets by Class

| Class | Tris | Materials | Texture |
|---|---|---|---|
| small prop | 300-3k | 1-2 | 512-1K |
| modular piece | 1-5k | 1 (atlas / trim) | trim sheet |
| weapon | 8-15k | 2-3 | 2K |
| vehicle | 30-50k | 3-5 | 2-4K |
| game character | 30-60k | 3-8 | 2-4K |
| hero character | 60-100k | 3-5 | 4K |
| mobile any | <= 10k | 1-2 | 1K |

| Platform cap | Value |
|---|---|
| UEFN static mesh | 20k tris per mesh without Nanite (Nanite: much higher, opaque only) |
| Roblox MeshPart | 20k tris and 10k verts per mesh; character head <= 4k tris |
| Web GLB | <= 30k tris, < 5 MB, WebP textures |
| Texel density | third person 512 px/m, hero 1024, mobile 256 |

## Reduction order (silhouette first)

1. Delete hidden faces (under other parts, inside, bottoms against the floor).
2. Merge by distance 0.0001 m, dissolve degenerate, delete loose.
3. Limited dissolve 1-5° on flat areas.
4. Cut cylinder sides: bolts 6-8, handles 12-16, barrels 24-32.
5. Decimate (collapse) last, ratio to budget, `use_symmetry=True` on symmetric assets.
6. Bake the lost detail to a normal map (`baking`).

```python
import bpy
def to_budget(obj, tris):
    now = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    if now > tris:
        m = obj.modifiers.new("budget", "DECIMATE"); m.ratio = tris / now; m.use_symmetry = True
        bpy.context.view_layer.objects.active = obj; bpy.ops.object.modifier_apply(modifier=m.name)
```

Adapted from Blender Agent Skills by EL4CTEO (optimization; MIT) and arjun988/blender-skills (LOD %; MIT).
