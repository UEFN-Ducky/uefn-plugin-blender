# UV workflow

Unwrap before materials and bake. Apply scale first — stretched UVs from unapplied scale are the #1 silent failure. All snippets via `blender_execute_blender_code` on Blender 4.5 LTS. Units: meters.

## Prep (always)

```python
import bpy
ob = bpy.data.objects["SM_Prop"]
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
if bpy.context.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
```

Ensure a UV map exists and is named clearly:

```python
me = ob.data
if not me.uv_layers:
    me.uv_layers.new(name="UVMap")
me.uv_layers.active = me.uv_layers["UVMap"]
# Lightmap channel (optional second set for UEFN)
if "UVLightmap" not in me.uv_layers:
    me.uv_layers.new(name="UVLightmap")
```

## Hard-surface / props — Smart UV Project

Good default for angular mid-poly. Angle 66–72°; island margin for mipmaps.

```python
import bpy
ob = bpy.data.objects["SM_Prop"]
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(
    angle_limit=1.22173,   # ~70° in radians
    island_margin=0.02,
    area_weight=0.0,
    correct_aspect=True,
    scale_to_bounds=False,
)
bpy.ops.object.mode_set(mode='OBJECT')
```

Then pack once for density:

```python
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.pack_islands(margin=0.02)
bpy.ops.object.mode_set(mode='OBJECT')
```

## Characters — manual seams

Mark seams at hairline, underarms, inner legs, clothing splits. Never rely on Smart Project for deforming heads.

```python
import bmesh
ob = bpy.data.objects["SK_Body"]
me = ob.data
bm = bmesh.new(); bm.from_mesh(me)
bm.edges.ensure_lookup_table()
# Example: mark selected edges as seams (set selection in edit mode first, or by index)
for e in bm.edges:
    if e.select:
        e.seam = True
bm.to_mesh(me); bm.free()

bpy.context.view_layer.objects.active = ob
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.02)
bpy.ops.object.mode_set(mode='OBJECT')
```

Tips:
- Straighten cylindrical limbs (follow active quads) after unwrap.
- Mirror-symmetric UVs when the mesh is mirrored — pack half, then mirror.
- Face UVs: keep eye/mouth islands readable; avoid diagonal stretch across lips.

## Texel density

Target a consistent px/m across a kit. Rough guide for 2K atlas:

| Asset class | Target |
|---|---|
| Hero character / weapon | 10–20 px/cm |
| Mid props | 5–10 px/cm |
| Modular env / trim | 2.5–5 px/cm (shared sheet) |

Check stretching in UV Editor (Display → Stretching → Area). Hot spots → cut more seams or relax.

## Lightmap UV (UEFN)

Second UV set with **no overlaps**, generous padding, islands packed into 0–1. Often a looser unwrap of the same mesh:

```python
me = ob.data
me.uv_layers.active = me.uv_layers["UVLightmap"]
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.lightmap_pack(PREF_MARGIN_DIV=64)  # larger divisor = more padding
bpy.ops.object.mode_set(mode='OBJECT')
me.uv_layers.active = me.uv_layers["UVMap"]
```

## Don'ts

- Don't leave overlapping UVs on unique-textured hero assets (ok for mirrored trim / tiled).
- Don't unwrap before applying scale.
- Don't pack islands to zero margin — mips bleed.
- Don't skip a second UV when the asset needs UE lightmaps.

Next: `materials_shading` → `texture_bake` (if high→low) → `asset_qa`.
