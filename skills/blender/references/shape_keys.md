# Shape keys

Morph targets for faces, correctives, and blendshapes. Export with `skeletal_export` (FBX morphs). Via `blender_execute_blender_code`.

## Basics

```python
import bpy
ob = bpy.data.objects["SK_Head"]
# Basis
if not ob.data.shape_keys:
    ob.shape_key_add(name="Basis", from_mix=False)
key = ob.data.shape_keys
# Expression
sk = ob.shape_key_add(name="jawOpen", from_mix=False)
sk.value = 0.0
# Edit sk.data for target shape (or sculpt with shape key active)
```

Name clearly for engine: `jawOpen`, `eyeBlink_L`, `mouthSmile`. Avoid spaces.

## Edit a key

```python
import bpy
ob = bpy.data.objects["SK_Head"]
ob.active_shape_key_index = ob.data.shape_keys.key_blocks.find("jawOpen")
bpy.context.view_layer.objects.active = ob
bpy.ops.object.mode_set(mode='EDIT')
# move verts...
bpy.ops.object.mode_set(mode='OBJECT')
ob.data.shape_keys.key_blocks["jawOpen"].value = 0.0
```

## Corrective shapes

Driven by bone rotation (drivers) for elbow/shoulder collapse:

```python
import bpy
ob = bpy.data.objects["SK_Body"]
sk = ob.data.shape_keys.key_blocks["corrective_elbow_L"]
# Add driver on sk.value → pose bone rotation (set in UI or via driver API)
fcurve = sk.driver_add("value")
drv = fcurve.driver
drv.type = 'SCRIPTED'
var = drv.variables.new()
var.name = "rot"
var.targets[0].id = bpy.data.objects["RIG_Character"]
var.targets[0].data_path = 'pose.bones["upperarm_l"].rotation_euler[0]'
drv.expression = "max(0.0, rot * 1.2)"
```

Keep correctives subtle; prefer better weights when possible (`skinning_weights`).

## Facial set tips

- Isolate face mesh or use vertex group filters when sculpting keys.
- Mirror L→R for symmetric shapes when appropriate.
- Don't stack 50 micro keys if 12 phoneme/viseme + brows cover the ask.

## Export notes

- Basis must be index 0.
- Apply Armature **after** shape evaluation rules — for FBX, typical path: export with morphs enabled (`skeletal_export`).
- Don't apply modifiers that destroy shape keys before export.

## Don'ts

- Don't rename Basis casually.
- Don't leave keys at value 1.0 when binding/exporting unintentionally.
- Don't invent dozens of keys the user didn't request.

Next: `animation_actions` → `skeletal_export`.
