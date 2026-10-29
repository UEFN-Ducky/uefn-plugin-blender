---
description: "Export settings per target in bpy: UE5 / UEFN, Unity, Roblox, Godot, web GLB, OBJ, STL (mm) and USDZ, with axes, scale, smoothing, triangulation, normals convention and size caps, plus a one-call format converter"
metadata:
  label: "Format Matrix"
---

# Format Matrix

| Target | Format | Forward / Up | Scale | Other |
|---|---|---|---|---|
| UE5 / UEFN | FBX | -Y / Z | FBX_SCALE_ALL, 1.0 | smoothing Face, tangent space on, leaf bones off, DirectX normal maps |
| Unity | FBX | -Z / Y | FBX_SCALE_UNITS, apply transform (bake space) | leaf bones off, GL normal maps |
| Roblox | FBX | -Z / Y | FBX_SCALE_UNITS (Studio converts to studs, 1 stud = 0.28 m) | triangulate, <= 20k tris and 10k verts per mesh, GL normals |
| Godot | GLB | Y up (+Y, glTF) | metres | import hints in names (`godot-export`) |
| Web | GLB | Y up | metres | WebP q85 textures, <= 30k tris, < 5 MB |
| Generic / Blender | GLB | Y up | metres | |
| OBJ | OBJ | -Z / Y | metres | static only, MTL alongside |
| 3D print | STL | Y / Z | global_scale 1000 = millimetres | binary, one closed shell |
| Apple AR | USDZ | Y up | metres | `usd_export` with a `.usdz` path |

```python
import bpy
def export(path, target):
    sel = dict(use_selection=True)
    if target == "ue5":
        bpy.ops.export_scene.fbx(filepath=path, axis_forward="-Y", axis_up="Z", apply_scale_options="FBX_SCALE_ALL",
            mesh_smooth_type="FACE", use_tspace=True, add_leaf_bones=False, bake_anim_use_nla_strips=False,
            bake_anim_use_all_actions=True, **sel)
    elif target in ("unity", "roblox"):
        bpy.ops.export_scene.fbx(filepath=path, axis_forward="-Z", axis_up="Y", apply_scale_options="FBX_SCALE_UNITS",
            bake_space_transform=True, mesh_smooth_type="FACE", use_triangles=target == "roblox", add_leaf_bones=False, **sel)
    elif target in ("godot", "web", "generic"):
        extra = {"export_image_format": "WEBP", "export_image_quality": 85} if target == "web" else {}
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", export_yup=True, export_apply=True, **extra, **sel)
    elif target == "obj":
        bpy.ops.wm.obj_export(filepath=path, export_selected_objects=True, forward_axis="NEGATIVE_Z", up_axis="Y")
    elif target == "stl":
        bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True, global_scale=1000.0, forward_axis="Y", up_axis="Z")
    elif target == "usdz":
        bpy.ops.wm.usd_export(filepath=path, selected_objects_only=True, export_animation=True)
```

## Convert any file

Empty scene → import (`import_scene.fbx`, `import_scene.gltf`, `wm.obj_import`, `wm.stl_import(global_scale=0.001)`, `wm.usd_import`, `wm.alembic_import`) → select all → `export(path, target)`. Never write over the source file.

Adapted from Blender Agent Skills by EL4CTEO (export-pipelines; MIT), AgentPMT Blender 3D Modeling (format conversion; feature list only) and RobLe3/cc-blender-skill (export caps; MIT). Same targets as Forge `export` / `convert`.
