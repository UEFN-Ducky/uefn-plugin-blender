---
description: "Blender GLB settings for Godot 4 and the import-hint name suffixes: -col, -colonly, -convcolonly, -rigid, -noimp, -loop, -navmesh"
metadata:
  label: "Godot GLB Settings"
---

# Godot GLB Settings

```python
bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
    export_apply=True, export_tangents=True, export_skins=True, export_morph=True,
    export_animations=True, export_animation_mode="ACTIONS")
```

Metres, +Y up (glTF). Apply rotation and scale first. Godot generates mesh LODs itself: export LOD0 only.

| Name suffix | Godot creates |
|---|---|
| `Crate-col` | the mesh plus a trimesh StaticBody from it |
| `Crate_01-colonly` | an invisible StaticBody from this mesh (use for UCX-style hulls) |
| `Crate_01-convcolonly` | an invisible convex collider |
| `Crate-rigid` | a RigidBody3D |
| `Crate-noimp` | nothing (helper geometry) |
| `Walk-loop` (action) | a looping animation |
| `Floor-navmesh` | a NavigationRegion3D mesh |

A UCX hull `UCX_Crate_01` becomes `Crate_01-colonly` for Godot. Keep suffixes off the render mesh you want plain.

Adapted from Blender Agent Skills by EL4CTEO (export-pipelines; MIT) and arjun988/blender-skills (godot-export; MIT).
