# Environments (modular)

Walls, floors, ceilings, trim kits for level assembly in UEFN. Grid math and consistent pivots matter more than hero polycounts. Via `blender_execute_blender_code`.

## Rules

- Module sizes on a clean grid (e.g. 2 m / 4 m / 8 m).
- Pivot convention: **corner** (snap-friendly) or **center** — pick one per kit and stick to it.
- Shared trim sheets / few materials (`uv_workflow`, `materials_shading`).
- Name `SM_Wall_A`, `SM_Floor_01`, `SM_Trim_Cap` — export set only, no cutters.

## Define the module

```python
import bpy
from mathutils import Vector

w, h, d = 4.0, 3.0, 0.2   # meters
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
ob = bpy.context.active_object
ob.name = "SM_Wall_A"
ob.scale = (w, d, h)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

# Pivot at floor min corner (snap-friendly)
corner_local = Vector((
    min(v.co.x for v in ob.data.vertices),
    min(v.co.y for v in ob.data.vertices),
    min(v.co.z for v in ob.data.vertices),
))
corner_world = ob.matrix_world @ corner_local
bpy.context.scene.cursor.location = corner_world
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
ob.location = (0, 0, 0)
```

## Kit variants

1. Wall plain / window / door cutouts (boolean cutters in `COL_Cutters`, then apply — `hard_surface`).
2. Matching floor / ceiling thickness and grid.
3. Trim pieces that tile on the module edge (same texel density).
4. Socket markers: empty `SOCKET_*` at snap points if helpful for authors (don't export empties unless wanted).

## Dressing

Place prop instances for lookdev; don't unique every chair. For UEFN, export modular meshes + separate prop FBXs — not one mega merged room unless intentional.

## Don'ts

- Don't mix pivot conventions in one kit.
- Don't UV every module uniquely when a trim sheet works.
- Don't leave boolean cutters in the export collection.

Next: `lod_collision` → `asset_qa` → `uefn_export`.
