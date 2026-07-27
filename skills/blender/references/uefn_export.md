# Export from Blender → UEFN (static)

Ship static meshes as FBX (preferred) or glTF/GLB. Rigged/animated → `skeletal_export`. Run `asset_qa` first. Via `blender_execute_blender_code`, then UEFN `import_asset`.

## Prep

```python
import bpy
ob = bpy.data.objects["SM_Prop"]
bpy.context.view_layer.objects.active = ob
for o in bpy.context.selected_objects:
    o.select_set(False)
ob.select_set(True)
if bpy.context.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
```

- Scene units: **meters**.
- Export collection only (no cutters / highs / empties unless intentional).
- Simple Principled materials; textures on disk.

## FBX (static)

```python
import bpy
bpy.ops.export_scene.fbx(
    filepath=r"C:\path\to\SM_Prop.fbx",
    use_selection=True,
    apply_scale_options='FBX_SCALE_ALL',
    bake_space_transform=True,
    object_types={'MESH'},
    use_mesh_modifiers=True,
    mesh_smooth_type='FACE',
    use_tspace=True,
    embed_textures=False,
    path_mode='AUTO',
    axis_forward='-Z',
    axis_up='Y',
)
```

## glTF / GLB

```python
import bpy
bpy.ops.export_scene.gltf(
    filepath=r"C:\path\to\SM_Prop.glb",
    use_selection=True,
    export_format='GLB',
    export_apply=True,
    export_texcoords=True,
    export_normals=True,
    export_materials='EXPORT',
)
```

## Import into UEFN

1. `import_asset` (or Content Browser) into the project Content folder.
2. Modeling skill: `get_static_mesh_info`, `set_mesh_collision` if needed.
3. Rebuild materials in UEFN (**materials** pack) — don't expect complex Blender graphs.

## Failure table

| Symptom | Likely cause | Fix |
|---|---|---|
| Tiny / giant mesh | Units / scale not applied | Meters + apply scale; FBX_SCALE_ALL |
| Wrong orientation | Axis mismatch | forward `-Z`, up `Y` (FBX) |
| Black / missing textures | Paths not packed / not copied | Export textures beside FBX; fix paths |
| Faceted shading | No custom normals / smooth | Smooth + weighted normals; export tspace |
| Exploded mesh | Modifiers not applied / GN unrealized | Apply mods; see `geometry_nodes` |
| Bad collision | No proxy | `lod_collision` UCX boxes |

## Don'ts

- Don't export the whole scene when you meant one prop.
- Don't ship Multires / live Cloth / unrealized GN.
- Don't use this path for armatures — `skeletal_export`.
