---
description: "Retarget BVH mocap or another rig's action onto a UE5-named rig in bpy: BVH import at scale 0.01, name map (Mixamo, CMU, Unity to Manny), Copy Rotation constraints, hips travel scaled by leg ratio, bake, decimate 0.3 to 0.5"
metadata:
  label: "Retarget Mocap"
---

# Retarget Mocap

1. Import: `bpy.ops.import_anim.bvh(filepath=p, global_scale=0.01, axis_forward="-Z", axis_up="Y", update_scene_fps=False, use_fps_scale=True)` (CMU/most BVH are in cm; 0.01 gives metres). Resample to 30 fps.
2. Match rest poses: both T-pose (or both A-pose). Pose the target to the source's frame-0 stance if not.
3. Map names (strip `mixamorig:`, compare lowercase without symbols):

| Source | Target |
|---|---|
| Hips | pelvis |
| Spine / Spine1 / Spine2 | spine_01 / spine_02 / spine_03 |
| Neck / Head | neck_01 / head |
| LeftShoulder / LeftArm / LeftForeArm / LeftHand | clavicle_l / upperarm_l / lowerarm_l / hand_l |
| LeftUpLeg / LeftLeg / LeftFoot / LeftToeBase | thigh_l / calf_l / foot_l / ball_l |

   (and Right → `_r`; CMU `LHipJoint`, `LowerBack` have no target: fold them into the child.)
4. Per mapped bone: Copy Rotation constraint (World Space ↔ World Space) to the source bone; on `pelvis` also Copy Location with influence, offset by the rest difference.
5. Hips travel: multiply the source hips translation by `target leg length / source leg length` (thigh→calf→foot heads), or the feet slide.
6. Bake: Pose → Animation → Bake Action, visual keying, clear constraints, every frame.
7. Reduce: keep 30-50 % of keys (Graph Editor Decimate ratio 0.3-0.5), then check foot contacts in a render.

```python
import bpy, re
def norm(n): return re.sub(r"[^a-z0-9]", "", n.split(":")[-1].lower())
ALIAS = {"hips": "pelvis", "spine": "spine_01", "spine1": "spine_02", "spine2": "spine_03", "neck": "neck_01", "head": "head"}
for s, side in (("l", "left"), ("r", "right")):
    for a, b in (("shoulder", "clavicle"), ("arm", "upperarm"), ("forearm", "lowerarm"), ("hand", "hand"),
                 ("upleg", "thigh"), ("leg", "calf"), ("foot", "foot"), ("toebase", "ball")):
        ALIAS[side + a] = f"{b}_{s}"

def constrain(src_arm, dst_arm):
    for pb in src_arm.pose.bones:
        dst = ALIAS.get(norm(pb.name))
        if dst and dst in dst_arm.pose.bones:
            c = dst_arm.pose.bones[dst].constraints.new("COPY_ROTATION")
            c.target, c.subtarget, c.target_space, c.owner_space = src_arm, pb.name, "WORLD", "WORLD"
```

Between two rigs with the same names and world-aligned rests, copy the action and scale only the root/pelvis location keys by the height ratio.

Adapted from Blender Agent Skills by EL4CTEO (animation, retargeting; MIT). Same mapping as Forge `retarget`.
