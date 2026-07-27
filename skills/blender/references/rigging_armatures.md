# Rigging armatures

Build armatures in code for game characters / props. Blender 4.x uses **bone collections** (not legacy armature layers). After bones: `skinning_weights` → `animation_actions` → `skeletal_export`. Via `blender_execute_blender_code`.

## Create armature + bones

```python
import bpy
from mathutils import Vector

bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
arm_ob = bpy.context.active_object
arm_ob.name = "RIG_Character"
arm = arm_ob.data
arm.name = "RIG_Character"

# Edit bones
eb = arm.edit_bones
root = eb[0]
root.name = "root"
root.head = Vector((0, 0, 0))
root.tail = Vector((0, 0, 0.2))

spine = eb.new("spine_01")
spine.head = Vector((0, 0, 1.0))
spine.tail = Vector((0, 0, 1.25))
spine.parent = root

thigh_l = eb.new("thigh_l")
thigh_l.head = Vector((0.15, 0, 1.0))
thigh_l.tail = Vector((0.15, 0, 0.5))
thigh_l.parent = spine

bpy.ops.object.mode_set(mode='OBJECT')
```

Naming: Epic/UE-friendly (`thigh_l`, `spine_01`, `hand_r`) beats random `Bone.001`. Keep a clear hierarchy: root → pelvis/spine → limbs.

## Bone collections (4.x)

```python
import bpy
arm = bpy.data.objects["RIG_Character"].data
# Ensure collection
if "DEF" not in arm.collections:
    arm.collections.new("DEF")
col = arm.collections["DEF"]
for b in arm.bones:
    col.assign(b)
# Hide helper collections in pose as needed
```

Legacy `arm.layers[...]` is gone — don't use it.

## Constraints (IK / copy)

```python
import bpy
arm_ob = bpy.data.objects["RIG_Character"]
bpy.context.view_layer.objects.active = arm_ob
bpy.ops.object.mode_set(mode='POSE')
pb = arm_ob.pose.bones.get("shin_l")
if pb:
    c = pb.constraints.new('IK')
    c.target = arm_ob
    c.subtarget = "ik_foot_l"   # control bone
    c.chain_count = 2
bpy.ops.object.mode_set(mode='OBJECT')
```

Keep a DEF (deform) chain and optional CTRL bones. Only deform bones should have `use_deform = True` for export.

```python
for b in arm.bones:
    b.use_deform = b.name.startswith(("root", "spine", "thigh", "shin", "foot", "upperarm", "forearm", "hand", "head", "clavicle", "toe"))
```

## Rigify (optional)

OK for lookdev; for UEFN often strip to deform bones only before export. Don't ship every Rigify widget into engine without cleanup.

## Don'ts

- Don't skin before hierarchy / roll is sane.
- Don't leave `Bone.001` names on a shippable rig.
- Don't use obsolete armature layers API.

Next: `skinning_weights` → `shape_keys` (optional) → `animation_actions`.
