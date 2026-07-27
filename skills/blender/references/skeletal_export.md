# Skeletal export (Blender → UEFN)

Rigged meshes, morphs, and animations via FBX. Static-only → `uefn_export`. Run `asset_qa` + weight checks first. Via `blender_execute_blender_code`.

## Prep

- Apply mesh scale; armature at rest pose (pose clear) for bind pose export when shipping skin.
- Deform bones only (`use_deform`); name UE-friendly.
- Limit weights (`skinning_weights`).
- Actions baked if they rely on IK (`animation_actions`).
- Units: meters.

```python
import bpy
rig = bpy.data.objects["RIG_Character"]
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.select_all(action='SELECT')
bpy.ops.pose.transforms_clear()
bpy.ops.object.mode_set(mode='OBJECT')
```

## FBX — mesh + armature

```python
import bpy
# Select rig + meshes
for o in bpy.context.selected_objects:
    o.select_set(False)
bpy.data.objects["RIG_Character"].select_set(True)
bpy.data.objects["SK_Body"].select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects["RIG_Character"]

bpy.ops.export_scene.fbx(
    filepath=r"C:\path\to\SK_Character.fbx",
    use_selection=True,
    apply_scale_options='FBX_SCALE_ALL',
    bake_space_transform=False,      # careful with armatures; prefer False + correct axes
    object_types={'ARMATURE', 'MESH'},
    use_mesh_modifiers=True,
    mesh_smooth_type='FACE',
    add_leaf_bones=False,
    primary_bone_axis='Y',
    secondary_bone_axis='X',
    armature_nodetype='NULL',
    bake_anim=False,                 # mesh+rig only
    use_armature_deform_only=True,
    axis_forward='-Z',
    axis_up='Y',
)
```

## FBX — animation

```python
import bpy
# Active action on armature; select armature
rig = bpy.data.objects["RIG_Character"]
for o in bpy.context.selected_objects:
    o.select_set(False)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig

bpy.ops.export_scene.fbx(
    filepath=r"C:\path\to\A_Idle.fbx",
    use_selection=True,
    object_types={'ARMATURE'},
    bake_anim=True,
    bake_anim_use_all_actions=False,
    bake_anim_use_nla_strips=False,
    bake_anim_force_startend_keying=True,
    bake_anim_simplify_factor=0.0,
    add_leaf_bones=False,
    use_armature_deform_only=True,
    axis_forward='-Z',
    axis_up='Y',
)
```

Morph/shape keys: include MESH in export with shape keys present; enable morph export options if exposed by your Blender build (`use_mesh` morphs — verify in export UI if flags differ). Prefer one skin FBX + separate anim FBXs for UE pipelines.

## UEFN import

1. Import skeletal mesh FBX into Content.
2. Create/assign Skeleton; reimport anims onto that skeleton.
3. Check orientation / T-pose vs A-pose match.
4. Materials rebuild in UEFN.

## Failure table

| Symptom | Fix |
|---|---|
| Mesh doesn't move | Weights / armature modifier / deform-only export |
| Extra bones | `add_leaf_bones=False`, deform-only |
| Tiny character | Apply scale; meters; FBX scale options |
| Anim wrong orientation | Axes; rest pose; bake visual keys |
| Morphs missing | Shape keys on mesh; export with mesh |

## Don'ts

- Don't use `uefn_export` static path for skinned assets.
- Don't export Rigify junk bones without stripping.
- Don't leave IK constraints as the only anim source without baking.
