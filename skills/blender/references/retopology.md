# Retopology

Turn sculpt / AI / Studio meshes into game-ready quads with deformation-friendly edge flow. High poly stays as Shrinkwrap target; low is what you UV, skin, and export. Via `blender_execute_blender_code`.

## Pipeline

1. Lock proportions (`blockout` / sculpt massing).
2. Keep high as reference (hide from render if needed).
3. Build new low mesh on surface (manual or QuadriFlow for rigid).
4. Edge flow for joints / face → load `face_topology` / `body_anatomy` / `hands_feet`.
5. `uv_workflow` → `texture_bake` → `skinning_weights` if rigged.

## Shrinkwrap target setup

```python
import bpy
high = bpy.data.objects["SM_High"]
low = bpy.data.objects["SM_Low"]   # retopo mesh

mod = low.modifiers.new("RetopoWrap", 'SHRINKWRAP')
mod.target = high
mod.wrap_method = 'PROJECT'          # or 'NEAREST_SURFACEPOINT'
mod.use_negative_direction = True
mod.use_positive_direction = True
mod.offset = 0.0
# Keep live while editing; apply only when topology locked
```

Snap during edit (optional): enable snapping to Face + Project onto high in the 3D View — or rely on Shrinkwrap + occasional apply/rebind.

## QuadriFlow (rigid props / rocks)

OK for non-deforming. Poor for faces and joints — always hand-fix those.

```python
import bpy
ob = bpy.data.objects["SM_High"]
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
bpy.ops.object.mode_set(mode='OBJECT')
# Remesh → Quad (QuadriFlow); face count target ~ game LOD0
bpy.ops.object.quadriflow_remesh(target_faces=4000, use_mesh_symmetry=True)
ob.name = "SM_Low"
```

After auto remesh: run `mesh_cleanup`, check poles at elbows/knees, fix n-gons on curved areas.

## Manual retopo pattern (characters)

- Start from a plane / poly build on the surface.
- Quads only on deforming regions; even spacing.
- Edge loops follow muscle/joint rotation (elbows, knees, mouth, eyelids).
- Poles (5+ junctions) live in flat areas, not on sharp bends.
- Symmetry: work half + Mirror modifier until form locks, then apply.

Deformation test before UV: temporary armature or bend bones — if mesh collapses, fix flow now.

## Transfer data from high

Normals / vertex colors / UVs (if any) after topology locks:

```python
import bpy
low = bpy.data.objects["SM_Low"]
high = bpy.data.objects["SM_High"]
for o in (high, low):
    o.select_set(True)
bpy.context.view_layer.objects.active = low
bpy.ops.object.data_transfer(
    data_type='CUSTOM_NORMAL',
    use_auto_transform=False,
    use_object_transform=True,
    mix_mode='REPLACE',
)
```

Prefer baking normals (`texture_bake`) over custom normals for UEFN statics.

## AI / Studio mesh triage

Raw Tripo/TRELLIS/Hyper3D meshes: dense tris, bad flow, often non-manifold.
1. `mesh_cleanup` (doubles, non-manifold).
2. Decimate or remesh for manageability.
3. Retopo — **never** skin a raw AI mesh for a deforming character.
4. Then UV / bake / export.

## Don'ts

- Don't export Multires level N or raw sculpt density to UEFN.
- Don't skip joint loops on characters.
- Don't apply Shrinkwrap until you're done moving verts.

Next: `uv_workflow` → `texture_bake` → (optional) `rigging_armatures`.
