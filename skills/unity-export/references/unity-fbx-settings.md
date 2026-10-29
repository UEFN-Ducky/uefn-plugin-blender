---
description: "Exact Blender FBX settings for Unity: Forward -Z, Up Y, FBX_SCALE_UNITS with Apply Transform so objects import at scale 1 and rotation 0, leaf bones off, _LOD0 naming for LODGroup, Humanoid avatar mapping notes"
metadata:
  label: "Unity FBX Settings"
---

# Unity FBX Settings

| Setting | Value |
|---|---|
| Apply Scalings | FBX Units Scale |
| Forward / Up | -Z / Y |
| Apply Transform | on (bake space transform): no -90 X rotation, scale 1 in Unity |
| Smoothing | Face |
| Add Leaf Bones | off |
| Bake Animation | All Actions, NLA strips off |
| Normal maps | OpenGL (green up), same as Blender |

```python
bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_scale_options="FBX_SCALE_UNITS",
    axis_forward="-Z", axis_up="Y", bake_space_transform=True, mesh_smooth_type="FACE",
    add_leaf_bones=False, bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False)
```

- LODs: name meshes `Name_LOD0`, `Name_LOD1`…; Unity builds the LODGroup on import (`lod-pipeline/references/lod-chain-recipe.md`).
- Collision: leave UCX_ hulls out; add MeshCollider (Convex) or primitive colliders on the prefab.
- Humanoid: Rig tab → Animation Type Humanoid → Configure. UE Manny names (pelvis, spine_01, thigh_l…) and Mixamo names auto-map; needs hips, spine, chest optional, head, upper/lower arms and legs, hands, feet. T-pose at rest.
- Clips: one action per clip, `AN_Char_Action`; tick Loop Time per looping clip in the importer.

Adapted from Blender Agent Skills by EL4CTEO (export-pipelines; MIT) and arjun988/blender-skills (unity-export; MIT).
