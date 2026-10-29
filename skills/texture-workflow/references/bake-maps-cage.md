---
description: "High-to-low baking in Cycles with exact settings: cage extrusion 3 % of the diagonal, ray distance 2× extrusion, margin 16 px, normal/AO/curvature/ID/thickness maps (emission tricks for the last three), a miss-percentage check, vertex-colour bakes, bake prep and an artefact → fix table"
metadata:
  label: "Bake Maps and Cage"
---

# Bake Maps and Cage

Prep: low-poly UVs with seams on every hard edge (`uv-workflow` → `uv-seams-texel-pack`), names `X_low` / `X_high`, touching parts exploded apart by the same offset on both, mirrored halves moved +1 U.

```python
import bpy

def bake(low, high, kind="NORMAL", size=2048, extrusion=0.03, ray=0.06, margin=16, cage=None):
    sc = bpy.context.scene; sc.render.engine = "CYCLES"
    sc.cycles.samples = 1 if kind in ("NORMAL", "EMIT") else 16
    sc.cycles.use_denoising = False
    diag = low.dimensions.length
    img = bpy.data.images.new(f"T_{low.name}_{kind}", size, size)
    img.colorspace_settings.name = "Non-Color"
    for m in low.data.materials:  # the active Image Texture node is the bake target
        n = m.node_tree.nodes.new("ShaderNodeTexImage"); n.image = img; m.node_tree.nodes.active = n
    for o in bpy.context.view_layer.objects: o.select_set(False)
    high.select_set(True); low.select_set(True); bpy.context.view_layer.objects.active = low
    kw = dict(use_cage=cage is not None, cage_object=cage.name if cage else "")
    bpy.ops.object.bake(type=kind, use_selected_to_active=True, cage_extrusion=extrusion * diag,
                        max_ray_distance=ray * diag, margin=margin, margin_type="EXTEND",
                        normal_space="TANGENT", **kw)
    return img
```

| Map | How | Notes |
|---|---|---|
| normal | `type="NORMAL"` | UE/UEFN: flip G (DirectX); Unity/Godot/glTF keep OpenGL |
| AO | `type="AO"`, 16 samples | goes to ORM R |
| curvature | high-poly material → Emission ← Map Range(Geometry.Pointiness, 0.42-0.58 → 0-1); `type="EMIT"` | convex white, flat 0.5 |
| ID | each high-poly material → Emission of one flat hue; `type="EMIT"` | masks for texturing |
| thickness | Emission ← Ambient Occlusion (Inside on, Only Local, distance 25 % of diagonal); `type="EMIT"` | white = thick; SSS / translucency |
| vertex colours | add a Color Attribute, set active, `bake(..., target="VERTEX_COLORS")` | AO or tint without UVs (mobile, LOD) |

**Miss check:** bake once with the low emitting white (no high, margin 0) = coverage mask; again from the high emitting white (selected-to-active, margin 0). Texels white in the mask and black in the second missed the high-poly. Erode the mask by 1 px (island borders), then misses / inside. Under 3 % is clean; above, raise extrusion or use a cage.

Settings: margin 16 px at 2k (2× the UV pack margin), cage = a copy of the low pushed out (Displace or Solidify offset), same topology.

| Looks like | Cause | Fix |
|---|---|---|
| wavy lines on cylinders | too few low sides | 24-32 sides or a cage |
| skewed bolts | rays follow smoothed normals | cage; support loop near the edge |
| black patches | rays miss | extrusion / ray up; miss check |
| bumps inverted in UE | wrong green | flip G for DirectX |
| seam lines | hard edge inside an island; small margin | seam hard edges; margin 16+ |
| banding | 8-bit gradient | bake 2× and downscale, or 16-bit PNG |
| neighbour's detail | ray too long | explode; ray 2× extrusion |

Adapted from Blender Agent Skills by EL4CTEO (baking; MIT). Same maps as Forge `bake(maps, cage, extrusion, ray, margin_px, to)`.
