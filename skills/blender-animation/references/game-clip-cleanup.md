---
description: "Game-ready clip cleanup in bpy: loop-seam check (under 1 degree), AN_ naming, strip bone scale keys, quaternion rotation, bake to every frame then reduce keys, NLA push-down per clip, root motion choice"
metadata:
  label: "Game Clip Cleanup"
---

# Game Clip Cleanup

| Rule | Value |
|---|---|
| Name | `AN_<Char>_<Action>[_<Variant>]`, one action per clip |
| Loop seam | last frame = first frame; max bone difference < 1° and < 0.5 cm |
| Bone scale | never keyed |
| Rotation mode | Quaternion on deform bones (no gimbal flips in the engine) |
| Keys | baked every frame (`step 1`), then reduced within 0.1° / 0.1 cm |
| Root motion | travel only on `root`; in-place cycles keep `root` still |
| fps | 30 unless the project says otherwise |

```python
import bpy, math

def loop_seam(arm, action):
    arm.animation_data.action = action
    f0, f1 = map(int, action.frame_range)
    def pose(f):
        bpy.context.scene.frame_set(f)
        return {b.name: (b.matrix_basis.to_quaternion(), b.matrix_basis.translation.copy()) for b in arm.pose.bones}
    a, b = pose(f0), pose(f1)
    deg = max(math.degrees(a[n][0].rotation_difference(b[n][0]).angle) for n in a)
    cm = max((a[n][1] - b[n][1]).length * 100 for n in a if n != "root")
    return deg, cm  # pass: deg < 1 and cm < 0.5

def clean(arm, action, tol=0.1):
    for fc in [fc for fc in action.fcurves if fc.data_path.endswith(".scale")]:
        action.fcurves.remove(fc)
    for b in arm.pose.bones: b.rotation_mode = "QUATERNION"
    bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.select_all(action="SELECT")
    bpy.ops.nla.bake(frame_start=int(action.frame_range[0]), frame_end=int(action.frame_range[1]), step=1,
                     only_selected=False, visual_keying=True, clear_constraints=True, use_current_action=True,
                     bake_types={"POSE"})
    bpy.ops.object.mode_set(mode="OBJECT")
```

Headless key reduction: for each F-curve, walk the keys and drop key *i* when the straight line between the last kept key and key *i+1* passes within `tol` of it. In the UI: Graph Editor → Key → Decimate (Allowed Change 0.1).

Then push down per clip: `track = arm.animation_data.nla_tracks.new(); track.strips.new(action.name, int(action.frame_range[0]), action)`, mute all but one when exporting a single clip, or export with All Actions and NLA strips off.

Adapted from Blender Agent Skills by EL4CTEO (animation; MIT) and arjun988/blender-skills (blender-animation; MIT). Same rules as Forge `clip` seam check and `bake_clip`.
