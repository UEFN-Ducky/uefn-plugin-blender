# Skinning weights

Bind mesh to armature, paint/limit influences, transfer weights. Game meshes: typically ≤4 influences per vertex for UE. Via `blender_execute_blender_code`.

## Parent with automatic weights

```python
import bpy
mesh = bpy.data.objects["SK_Body"]
rig = bpy.data.objects["RIG_Character"]
for o in bpy.context.selected_objects:
    o.select_set(False)
mesh.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
```

Requires mesh near the bones; apply mesh scale first. Fix bad auto weights by hand (Weight Paint) or transfer from a known-good mesh.

## Armature modifier (explicit)

```python
import bpy
mesh = bpy.data.objects["SK_Body"]
rig = bpy.data.objects["RIG_Character"]
mod = mesh.modifiers.get("Armature") or mesh.modifiers.new("Armature", 'ARMATURE')
mod.object = rig
mod.use_vertex_groups = True
mesh.parent = rig
```

Vertex groups must match deform bone names.

## Limit influences

```python
import bpy
ob = bpy.data.objects["SK_Body"]
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
bpy.ops.object.vertex_group_limit_total(limit=4)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
bpy.ops.object.mode_set(mode='OBJECT')
```

## Transfer weights

```python
import bpy
src = bpy.data.objects["SK_Body"]      # good weights
dst = bpy.data.objects["SK_Shirt"]     # garment
for o in (src, dst):
    o.select_set(True)
bpy.context.view_layer.objects.active = dst
bpy.ops.object.data_transfer(
    data_type='VGROUP_WEIGHTS',
    use_auto_transform=False,
    use_object_transform=True,
    layers_select_src='ALL',
    layers_select_dst='NAME',
    mix_mode='REPLACE',
)
```

Then limit/normalize on the destination.

## Quick weight audit

```python
import bpy
ob = bpy.data.objects["SK_Body"]
me = ob.data
bad = 0
for v in me.vertices:
    total = sum(g.weight for g in v.groups)
    if total < 0.001:
        bad += 1
print("zero-weight verts:", bad, "of", len(me.vertices))
```

Pose stress-test: rotate joints, screenshot (`verify_loop`). Fix elbows/knees/shoulders first.

## Don'ts

- Don't export with >4 heavy influences if the project forbids it.
- Don't leave clothing unweighted (flies in world space).
- Don't bind before retopo is locked.

Next: `shape_keys` (optional) → `animation_actions` → `skeletal_export`.
