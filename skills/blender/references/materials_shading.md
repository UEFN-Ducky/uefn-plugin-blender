# Materials / shading

Principled BSDF PBR for game-like lookdev in Blender. UEFN rebuilds materials after import — keep graphs simple, bake complexity into textures. Snippets via `blender_execute_blender_code`. Blender 4.2–5.0: Principled socket names below are current (no `Specular` → use `Specular IOR Level`; Transmission is `Transmission Weight`).

## Create + assign

```python
import bpy
ob = bpy.data.objects["SM_Prop"]
mat = bpy.data.materials.get("MAT_Metal") or bpy.data.materials.new("MAT_Metal")
mat.use_nodes = True
nt = mat.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (300, 0)
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (0, 0)
nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

bsdf.inputs["Base Color"].default_value = (0.7, 0.7, 0.7, 1)
bsdf.inputs["Metallic"].default_value = 1.0
bsdf.inputs["Roughness"].default_value = 0.35
bsdf.inputs["Specular IOR Level"].default_value = 0.5

if ob.data.materials:
    ob.data.materials[0] = mat
else:
    ob.data.materials.append(mat)
```

One material per logical surface when possible. Name `MAT_*`.

## Image textures (Base / Rough / Normal)

```python
import bpy, os
mat = bpy.data.materials["MAT_Metal"]
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

def tex(path, non_color=False, loc=( -400, 0)):
    n = nt.nodes.new("ShaderNodeTexImage")
    n.location = loc
    img = bpy.data.images.load(path, check_existing=True)
    n.image = img
    if non_color:
        n.image.colorspace_settings.name = 'Non-Color'
    return n

base = tex(r"C:\path\T_Metal_BC.png", loc=(-400, 200))
rough = tex(r"C:\path\T_Metal_R.png", non_color=True, loc=(-400, 0))
nrm = tex(r"C:\path\T_Metal_N.png", non_color=True, loc=(-400, -200))
nrm_node = nt.nodes.new("ShaderNodeNormalMap"); nrm_node.location = (-150, -200)

nt.links.new(base.outputs["Color"], bsdf.inputs["Base Color"])
nt.links.new(rough.outputs["Color"], bsdf.inputs["Roughness"])
nt.links.new(nrm.outputs["Color"], nrm_node.inputs["Color"])
nt.links.new(nrm_node.outputs["Normal"], bsdf.inputs["Normal"])
```

Packed ORM (R=AO, G=Rough, B=Metal) — split with Separate Color:

```python
sep = nt.nodes.new("ShaderNodeSeparateColor"); sep.location = (-200, 0)
# link ORM Color → sep.inputs["Color"]
# sep.outputs["Green"] → Roughness; sep.outputs["Blue"] → Metallic
# AO → Mix with Base Color or leave for UE
```

## Viewport for verify screenshots

```python
import bpy
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'MATERIAL'   # or 'RENDERED'
```

Use Material Preview for albedo/rough read; Solid + Flat for silhouette (`verify_loop`).

## Smooth shading + attribute

```python
ob = bpy.data.objects["SM_Prop"]
for poly in ob.data.polygons:
    poly.use_smooth = True
# Auto Smooth removed as mesh flag in 4.1+ — use Smooth by Angle modifier
mod = ob.modifiers.get("SmoothByAngle") or ob.modifiers.new("SmoothByAngle", 'NODES')
# Prefer: bpy.ops.object.shade_smooth_by_angle() with override, or Weighted Normal — see hard_surface
```

Practical path for mid-poly: `hard_surface` (Smooth by Angle + Weighted Normal). Don't fight with old `use_auto_smooth`.

## UEFN handoff

- Export textures as PNG/TGA; rebuild materials in UEFN (**materials** skill pack).
- Don't rely on complex Blender node graphs surviving FBX — bake to maps (`texture_bake`).
- Keep material slots ordered and named; empty slots confuse import.

## Don'ts

- Don't invent socket names from memory — if a set fails, list `list(bsdf.inputs.keys())`.
- Don't leave unused Image nodes with packed 8K textures — purge before ship.
- Don't use Emission for "fake metal" when Metallic + Roughness will do.

Next: `texture_bake` for high→low maps; `asset_qa` before `uefn_export`.
