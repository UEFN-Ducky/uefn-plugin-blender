# Animation actions

Keyframes, Actions, NLA, and bake for export. Blender **4.4+** slotted actions: one Action can hold multiple slots (object / armature). Prefer clear Action names (`A_Idle`, `A_Walk`). Via `blender_execute_blender_code`.

## Keyframe a pose

```python
import bpy
rig = bpy.data.objects["RIG_Character"]
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='POSE')
bpy.context.scene.frame_set(1)
for pb in rig.pose.bones:
    pb.keyframe_insert(data_path="location", frame=1)
    pb.keyframe_insert(data_path="rotation_quaternion", frame=1)
    # or rotation_euler if that's the mode
bpy.ops.object.mode_set(mode='OBJECT')
```

Set rotation mode explicitly when mixing tools:

```python
for pb in bpy.data.objects["RIG_Character"].pose.bones:
    pb.rotation_mode = 'QUATERNION'
```

## Actions

```python
import bpy
rig = bpy.data.objects["RIG_Character"]
action = bpy.data.actions.get("A_Idle") or bpy.data.actions.new("A_Idle")
# Assign — Blender 4.4+ slotted API:
if hasattr(rig, "animation_data") and rig.animation_data is None:
    rig.animation_data_create()
ad = rig.animation_data
ad.action = action
# 4.4+ slots (if available): ensure armature slot is active — UI: Action editor
```

Duplicate / push down to NLA for multi-clip files when needed.

## Bake for export

Control rig → deform bones, or constraints → keys:

```python
import bpy
rig = bpy.data.objects["RIG_Character"]
bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode='POSE')
bpy.ops.nla.bake(
    frame_start=1,
    frame_end=60,
    only_selected=False,
    visual_keying=True,
    clear_constraints=False,
    clear_parents=False,
    use_current_action=True,
    bake_types={'POSE'},
)
bpy.ops.object.mode_set(mode='OBJECT')
```

Bake a clean Action before FBX if IK/constraints won't evaluate in-engine.

## Frame range

```python
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 60
scene.frame_current = 1
```

## Don'ts

- Don't leave muted NLA strips as the only source without baking.
- Don't mix root motion accidentally (decide: in anim vs in Verse).
- Don't export with wrong FPS vs UEFN project without noting it.

Next: `skeletal_export`.
