# Import assets into Blender

Bring FBX / glTF / OBJ / USD / AI meshes into Blender, fix scale/axes, clean, then route to modeling or `uefn_export`. Via `blender_execute_blender_code`.

## FBX

```python
import bpy
bpy.ops.import_scene.fbx(
    filepath=r"C:\path\model.fbx",
    automatic_bone_orientation=True,
    use_anim=True,
)
# Imported objects are selected
for ob in bpy.context.selected_objects:
    print(ob.name, ob.type)
```

## glTF / GLB

```python
import bpy
bpy.ops.import_scene.gltf(filepath=r"C:\path\model.glb")
```

## OBJ

```python
import bpy
bpy.ops.wm.obj_import(filepath=r"C:\path\model.obj")  # 4.x operator
```

## Scale / axes triage

```python
import bpy
# Scene meters
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0

ob = bpy.context.active_object
# If tiny/giant: scale then apply
if ob:
    # Example: cm-authored asset → meters
    # ob.scale *= 0.01
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
```

Sketchfab / random market packs: always measure a known edge (`measure` mindset — compare to 1.8 m human empty). Set `target_size` when using Sketchfab MCP download tools.

## AI / Studio mesh cleanup

Tripo / TRELLIS / Hyper3D / Hunyuan imports are dense and messy:

1. Rename `SM_*`, move to working collection (`scene_organization`).
2. `mesh_cleanup` — doubles, non-manifold, normals.
3. Decimate or remesh if unmanageable.
4. **Deforming character?** → `retopology` (never skin raw AI mesh).
5. Rigid prop? Mid-poly cleanup + `uv_workflow` may be enough.
6. Then materials / bake / export.

## Join / separate

```python
import bpy
# Join selected meshes
bpy.ops.object.join()
# Separate by loose parts
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.separate(type='LOOSE')
bpy.ops.object.mode_set(mode='OBJECT')
```

## Don'ts

- Don't assume import units are meters.
- Don't skin or animate a raw AI mesh.
- Don't leave packed junk materials — rename `MAT_*`, purge orphans.

Next: discipline subskill → `asset_qa` → `uefn_export` / `skeletal_export`.
