# Ducky bpy — LOD generation

Run snippets via `blender_execute_blender_code`. Budgets/process: this pack's other references.

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
