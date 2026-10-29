---
description: "Game rig check in bpy (UE5 Manny or Roblox R15 names, one root, L/R mirror, unweighted verts, more than 4 influences, idle bones, bone scale keys), bone-heat fallbacks (10x scale trick under 50 cm, voxel proxy plus Data Transfer) and a stress-pose clip"
metadata:
  label: "Rig Check and Weight Fallbacks"
---

# Rig Check and Weight Fallbacks

## Check

| Check | Pass |
|---|---|
| names | UE5/UEFN/Unity: pelvis spine_01 head upperarm/lowerarm/hand/thigh/calf/foot _l _r. Roblox R15: LowerTorso UpperTorso Head Left/RightUpperArm, LowerArm, Hand, UpperLeg, LowerLeg, Foot |
| roots | exactly one (`root` at the origin) |
| mirror | every `_l` has an `_r` with head x mirrored within 1 cm and the same height |
| unweighted | 0 verts with no deform weight |
| influences | <= 4 (UEFN, Unity, Roblox) or 8 (UE5) per vertex |
| idle bones | every deform leaf bone weighs something |
| scale keys | none in any action |

```python
import bpy
def rig_check(arm, mesh, limit=4):
    bones = {b.name: b for b in arm.data.bones}
    out = [f"missing {n}" for n in ("pelvis", "spine_01", "head", "thigh_l", "thigh_r", "hand_l", "hand_r") if n not in bones]
    if sum(b.parent is None for b in bones.values()) > 1: out.append("several roots")
    for n, b in bones.items():
        t = bones.get(n[:-2] + "_r") if n.endswith("_l") else None
        if n.endswith("_l") and (t is None or abs(b.head_local.x + t.head_local.x) > .01): out.append(f"{n} not mirrored")
    deform = {g.index for g in mesh.vertex_groups if g.name in bones}
    ws = [[g for g in v.groups if g.group in deform and g.weight > 1e-4] for v in mesh.data.vertices]
    out += [f"{sum(not w for w in ws)} unweighted"] if any(not w for w in ws) else []
    out += [f"{sum(len(w) > limit for w in ws)} verts > {limit}"] if any(len(w) > limit for w in ws) else []
    for a in bpy.data.actions:
        if any(fc.data_path.endswith(".scale") for fc in a.fcurves): out.append(f"{a.name} keys bone scale")
    return out
```

Fix influences: `bpy.ops.object.vertex_group_limit_total(limit=4)` then `vertex_group_normalize_all(lock_active=False)`.

## When bone heat fails

"Bone Heat Weighting: failed to find solution" comes from thresholds tuned for metre-sized bodies and from open or self-intersecting meshes.

1. **Small mesh (< 50 cm):** scale armature and mesh together 10x about the armature origin, Parent With Automatic Weights, scale back. Weights don't depend on scale.
2. **Open / intersecting mesh:** duplicate, add Remesh (Voxel, size = largest dimension / 48), apply, Automatic Weights on the proxy, then on the real mesh a Data Transfer modifier: Vertex Data → Vertex Groups, Nearest Face Interpolated, source = proxy, apply, delete the proxy.
3. Last resort: Envelope weights, then smooth (`vertex_group_smooth`, factor 0.5, 2 repeats).

## Stress poses

Key one action `Stress` and render frames 10/20/30/40: arms raised 80° (frame 10), elbows 140° (20), hips 90° + knees 150° (30), spine twist 45° (40), rest at 1 and 50. Look for candy-wrap twists, collapsing elbows, pelvis tearing.

Adapted from Blender Agent Skills by EL4CTEO (rigging; MIT) and arjun988/blender-skills (rigging; MIT). Same checks as Forge `rig_check`, `stress`, `auto_weights`.
