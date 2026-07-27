# Cloth

Default for games: **modeled shells** with folds (`character_clothing`). Cloth sim is a fold generator — pin, drape, freeze one frame, cleanup. Never ship a live Cloth modifier to UEFN. Via `blender_execute_blender_code`. Blender 4.x: Pin Group RNA is oddly named `vertex_group_mass` (“Vertex Group for pinning”).

## Modeled cloth (default)

Shell over body → Solidify → hand/sculpt folds → remove hidden faces. Load `character_clothing`.

## Sim → freeze

```python
import bpy

garment = bpy.data.objects["SM_Shirt"]
body = bpy.data.objects["SK_Body"]

# Body collision
if not any(m.type == 'COLLISION' for m in body.modifiers):
    body.modifiers.new("Collision", 'COLLISION')

# Pin group (weight 1.0 on shoulders / waist)
if "Pin" not in garment.vertex_groups:
    garment.vertex_groups.new(name="Pin")
# Assign pin weights in Edit Mode before running sim

mod = garment.modifiers.get("Cloth") or garment.modifiers.new("Cloth", 'CLOTH')
mod.settings.quality = 8
mod.settings.pin_stiffness = 1.0
mod.settings.vertex_group_mass = "Pin"   # Pin Group (yes, this RNA name)
mod.collision_settings.use_collision = True
mod.collision_settings.distance_min = 0.002
mod.point_cache.frame_start = 1
mod.point_cache.frame_end = 50

bpy.context.scene.frame_set(40)   # pick a settled frame after bake/play
bpy.context.view_layer.objects.active = garment
garment.select_set(True)
with bpy.context.temp_override(object=garment, active_object=garment, selected_objects=[garment]):
    bpy.ops.object.modifier_apply(modifier=mod.name)
```

Raise quality steps carefully (slow). If mesh explodes: lower time scale, increase collision distance, fix pin weights, check applied scale.

## After apply

- Run `mesh_cleanup` if messy.
- Check body intersection (`verify_loop` screenshots).
- Optional Solidify for thickness; delete inner faces that won't be seen.

## Don'ts

- Don't export a live Cloth modifier / point cache.
- Don't sim before proportions and body collider are locked.
- Don't pin nothing — garment falls through the world.

Next: `character_clothing` / `mesh_cleanup` → `uv_workflow` → export.
