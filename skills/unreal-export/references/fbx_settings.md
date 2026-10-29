---
description: "Exact Blender FBX settings for Unreal Engine 5 and UEFN: scale 1.0, Forward -Y, Up Z, FBX_SCALE_ALL, smoothing Face, tangent space, leaf bones off, all actions as takes, UCX_ and LOD naming, import options"
metadata:
  label: "UE5 FBX Settings"
---

# UE5 FBX Settings

Scene units: Metric, unit scale 1.0 (or 0.01 with centimetre modelling; pick one and keep it). Apply rotation and scale on every object before export.

| Setting | Value |
|---|---|
| Scale | 1.0, Apply Scalings = FBX All |
| Forward / Up | -Y / Z |
| Apply Transform | off (experimental; apply in Blender instead) |
| Smoothing | Face (Edge only with hard-edge workflows) |
| Tangent Space | on (needs triangles or quads, no n-gons) |
| Add Leaf Bones | off |
| Primary / Secondary bone axis | Y / X |
| Armature FBXNode type | Null |
| Bake Animation | on, All Actions, NLA strips off, force start/end keying |
| Path mode | Copy, embed textures off |

```python
bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH", "ARMATURE", "EMPTY"},
    global_scale=1.0, apply_scale_options="FBX_SCALE_ALL", axis_forward="-Y", axis_up="Z",
    mesh_smooth_type="FACE", use_tspace=True, add_leaf_bones=False, primary_bone_axis="Y", secondary_bone_axis="X",
    bake_anim=True, bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True)
```

- Names: `SM_` static, `SK_` skeletal, `AN_`/`AS_` clips, `UCX_SM_Name_01` collision (`ucx-naming.md`), `SM_Name_LOD0..3`.
- Armature object named `Armature` is dropped by UE as the root; name it anything else to keep a root bone, and have exactly one root (`root` at the origin).
- UE import: Import Uniform Scale 1.0, Normal Import Method "Import Normals and Tangents", Combine Meshes on for props, Auto Generate Collision off when you ship UCX_.
- Normal maps: DirectX (green down). Flip G from Blender's OpenGL bakes.

Then re-import with `export-pipeline/references/export-verify.md`.

Adapted from Blender Agent Skills by EL4CTEO (export-pipelines; MIT) and arjun988/blender-skills (unreal-export; MIT).
