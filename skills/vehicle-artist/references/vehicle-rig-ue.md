---
description: "Vehicle rig for UE Chaos Vehicles and UEFN: root plus FL/FR/RL/RR_wheel bones at the hub centres, door/hood/trunk hinge bones, rigid binding, export settings, LODs and UCX collision for cars"
metadata:
  label: "Vehicle rig for UE / UEFN"
---

# Vehicle rig for UE / UEFN

## Two ways to ship a car

| Target | Ship as | Moving parts |
|---|---|---|
| UE5 Chaos Vehicle | one **skeletal mesh** + physics asset | wheel bones spun by the vehicle component |
| UEFN | static meshes per part (or one skeletal for a prop car) | each part rotates about its own origin |

## Bones (metres in Blender; head at the pivot)

| Bone | Parent | Head | Tail |
|---|---|---|---|
| `root` | — | (0, 0, 0) ground centre | +Z 0.3 |
| `FL_wheel` `FR_wheel` `RL_wheel` `RR_wheel` | root | hub centre (±track/2, axle y, tyre r) | 0.15 outward on X |
| `door_FL` … `door_RR` | root | hinge line, front edge of the door | +Z 0.3 |
| `hood` | root | rear hinge at the windshield base | +Z 0.3 |
| `trunk` | root | front hinge of the deck lid | +Z 0.3 |

```python
import bpy
arm = bpy.data.armatures.new("SK_Car"); rig = bpy.data.objects.new("SK_Car", arm)
bpy.context.collection.objects.link(rig); bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="EDIT")
root = arm.edit_bones.new("root"); root.head = (0, 0, 0); root.tail = (0, 0, 0.3)
for tag, x, y in (("FL", .84, -1.52), ("FR", -.84, -1.52), ("RL", .84, 1.28), ("RR", -.84, 1.28)):
    b = arm.edit_bones.new(tag + "_wheel"); b.parent = root
    b.head = (x, y, 0.317); b.tail = (x + (0.15 if x > 0 else -0.15), y, 0.317)
bpy.ops.object.mode_set(mode="OBJECT")
```

## Binding: rigid, one bone per part

Every part gets one vertex group named for its bone with weight 1.0, plus an Armature modifier; wheel meshes to their wheel bone, doors (and their glass) to the door bone, calipers and everything else to `root`. No automatic weights on a car.

```python
for ob, bone in parts:                       # [(object, "FL_wheel"), (body, "root"), ...]
    g = ob.vertex_groups.new(name=bone); g.add(range(len(ob.data.vertices)), 1.0, "REPLACE")
    ob.modifiers.new("Armature", "ARMATURE").object = rig; ob.parent = rig
```

UE: in the Chaos Vehicle Blueprint set each wheel's **Bone Name** to `FL_wheel` …, wheel radius = tyre radius, width = tyre width. Physics asset: one convex body on `root`, spheres on the wheels (or none: Chaos raycasts). Export FBX: Armature Deform only, Add Leaf Bones off, scale 1.0, forward -Y, up Z.

## LODs and collision

| LOD | Ratio | Keep |
|---|---|---|
| LOD0 | 1.0 | everything, 40-120k tris hero |
| LOD1 | 0.5 | drop wipers, plates, interior detail |
| LOD2 | 0.25 | body + wheels + glass |
| LOD3 | 0.1 | one shell, wheels as 12-sided discs |

Collision: one `UCX_<Mesh>_01` convex hull of the body (48 directions) plus wheel spheres only if physics needs them; ≤ 10 UCX per mesh. See `vehicle-lod-targets.md`, `lod-pipeline`, `collision-proxy`.

**Done when:** posing `FL_wheel` 90° about X spins the wheel in place (screenshot, then rest pose), a door bone at 60° swings the door without leaving its hinge, and the FBX imports into UE with 5 + n bones and the LODs.

Forge: `car(...)` builds this rig (`<name>_Rig`), binds every part, stores LOD ratios and makes `UCX_<name>_01`.

---
Bone naming follows UE Chaos Vehicle wheel setups; rig workflow adapted from Blender Agent Skills (rigging, export-pipelines) by EL4CTEO, MIT licence.
