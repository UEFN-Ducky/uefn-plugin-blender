# LOD and collision

Build LOD chains and simple collision proxies before UEFN import. Apply scale first. Via `blender_execute_blender_code`.

## Budget guide (static meshes)

| Class | LOD0 tris (order of magnitude) |
|---|---|
| Tiny prop | 200–800 |
| Simple prop | 400–2,500 |
| Hero prop / weapon | 2,500–9,000 |
| Modular wall | 100–800 |
| Foliage cluster | keep scatter budget in mind |

Characters: follow project targets; deforming LODs need careful edge-flow preservation.

## LOD generation

```python
import bpy
src = bpy.data.objects["SM_Prop"]
bpy.context.view_layer.objects.active = src
src.select_set(True)
bpy.ops.object.duplicate()
lod1 = bpy.context.active_object
lod1.name = "SM_Prop_LOD1"
mod = lod1.modifiers.new("Decimate", 'DECIMATE')
mod.ratio = 0.5          # ~50% — tune to silhouette
with bpy.context.temp_override(object=lod1, active_object=lod1, selected_objects=[lod1]):
    bpy.ops.object.modifier_apply(modifier=mod.name)

bpy.ops.object.duplicate()
lod2 = bpy.context.active_object
lod2.name = "SM_Prop_LOD2"
mod2 = lod2.modifiers.new("Decimate", 'DECIMATE')
mod2.ratio = 0.3         # relative to LOD1 ≈ ~15% of LOD0 if chained from src instead
```

Better: always Decimate from LOD0 with ratios 0.5 / 0.15 so naming matches intent. Remove tiny greebles on LOD2+ (delete by size or hand).

Preserve UVs: Decimate Collapse usually keeps UVMap; verify packing. For characters prefer hand LODs or progressive tools — auto decimate wrecks joints.

## Collision proxies

Prefer boxes / capsules / simple convex pieces over direct mesh collision.

```python
import bpy
# Box proxy around bounds
ob = bpy.data.objects["SM_Prop"]
# Duplicate bounds as cube
from mathutils import Vector
coords = [ob.matrix_world @ v.co for v in ob.data.vertices]
min_c = Vector(map(min, zip(*coords)))
max_c = Vector(map(max, zip(*coords)))
center = (min_c + max_c) / 2
size = max_c - min_c
bpy.ops.mesh.primitive_cube_add(location=center)
proxy = bpy.context.active_object
proxy.name = "UCX_SM_Prop"          # UE-friendly prefix if using UCX convention
proxy.scale = size / 2
bpy.ops.object.transform_apply(scale=True)
proxy.display_type = 'WIRE'
```

Multiple convex pieces: `UCX_SM_Prop_01`, `_02`, … Export with mesh or let UEFN rebuild — still provide sensible proxies for gameplay.

## Don'ts

- Don't Decimate without applied scale.
- Don't keep boolean cutters / Multires on LOD exports.
- Don't use render mesh as collision for complex shapes.

Next: `asset_qa` → `uefn_export`.
