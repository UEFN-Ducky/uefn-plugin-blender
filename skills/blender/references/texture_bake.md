# Texture bake

High→low maps for game meshes. Requires clean UVs on the **low** (`uv_workflow`). Apply scale on both meshes. Via `blender_execute_blender_code`.

## Maps to bake

| Map | Engine use | Notes |
|---|---|---|
| Normal (Tangent) | Detail + curvature from high | Primary bake |
| AO | Multiply / cavity | Soften corners |
| Diffuse / Base Color | When high has color | Optional |
| Roughness / ID | Material masks | Optional |

UEFN: OpenGL-style normals; if green channel looks inverted in-engine, flip Y in the Normal Map node or re-bake with correct space.

## Setup

1. Low = active, selected. High also selected (or use cage).
2. Low has non-overlapping UVMap.
3. Create empty images on the low's material, then bake.

```python
import bpy

low = bpy.data.objects["SM_Low"]
high = bpy.data.objects["SM_High"]
# Selection: high first, low active (Blender Selected to Active convention)
for o in bpy.context.selected_objects:
    o.select_set(False)
high.select_set(True)
low.select_set(True)
bpy.context.view_layer.objects.active = low

# Image target
img = bpy.data.images.new("Bake_Normal", width=2048, height=2048, alpha=False, float_buffer=False)
mat = low.data.materials[0]
nt = mat.node_tree
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = img
nt.nodes.active = tex   # bake target = active image node

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
scene.cycles.bake_type = 'NORMAL'
scene.render.bake.use_selected_to_active = True
scene.render.bake.cage_extrusion = 0.05      # meters; raise if rays miss
scene.render.bake.margin = 16
scene.render.bake.normal_space = 'TANGENT'
# Optional cage mesh:
# scene.render.bake.use_cage = True
# scene.render.bake.cage_object = bpy.data.objects["SM_Cage"]

bpy.ops.object.bake(type='NORMAL')
img.filepath_raw = r"C:\path\T_Asset_N.png"
img.file_format = 'PNG'
img.save()
```

AO bake:

```python
scene.cycles.bake_type = 'AO'
img_ao = bpy.data.images.new("Bake_AO", 2048, 2048)
tex.image = img_ao
nt.nodes.active = tex
bpy.ops.object.bake(type='AO')
img_ao.filepath_raw = r"C:\path\T_Asset_AO.png"
img_ao.file_format = 'PNG'
img_ao.save()
```

## Cage vs extrusion

- **Extrusion** — quick; fails on thin shells / deep recesses (spikes, black).
- **Cage** — duplicate low, inflate along normals, assign as cage object. Best for characters.

```python
import bpy
low = bpy.data.objects["SM_Low"]
cage = low.copy()
cage.data = low.data.copy()
cage.name = "SM_Cage"
bpy.context.collection.objects.link(cage)
# Inflate in edit mode / displace slightly along normals, hide from render
```

## Explode bake

If parts ray-miss each other (fingers, overlapping plates), temporarily separate pieces along normals, bake, restore:

```python
# Translate each island object +0.5m on an axis, bake, translate back
for ob in parts:
    ob.location.x += 0.5
# bake...
for ob in parts:
    ob.location.x -= 0.5
```

## After bake

1. Assign maps in `materials_shading`.
2. Hide/delete high from export set (`scene_organization`).
3. Save `.blend` + image files to disk (unsaved Image datablocks vanish).

## Don'ts

- Don't bake before UVs / applied scale.
- Don't use EEVEE for Selected-to-Active normal bake — Cycles.
- Don't ship the high-poly Multires cage to UEFN.

Next: `materials_shading` → `asset_qa` → `uefn_export`.
