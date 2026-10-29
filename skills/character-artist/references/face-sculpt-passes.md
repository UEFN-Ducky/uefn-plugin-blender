---
description: "Head sculpt pass order with numbers: primary forms, secondary folds and wrinkles, tertiary pores; multires levels, brush sizes and headless bpy"
metadata:
  label: "Face sculpt passes"
---

# Face sculpt passes

Detail goes in strictly by frequency. A pass never starts until the one before reads right from 3 m in a grey render.

| Pass | What | Resolution | Brush size (H = 0.24 m) | Stop when |
|---|---|---|---|---|
| 1. Primary | skull, jaw, cheekbones, brow mass, nose block, lip volume | base quads (5–8k) | 0.03–0.06 m | silhouette front and side matches the refs (IoU ≥ 0.85) |
| 2. Secondary | nasolabial fold, lid creases, lip border, ear forms, philtrum, chin pad, neck tendons | multires 2 (≈ 80–120k) | 0.004–0.012 m | the planes read under one key light |
| 3. Tertiary | pores, fine wrinkles, lip lines, crow's feet | multires 4 (≈ 1–2M), or bake only | 0.0005–0.002 m | visible only at 30 cm; bake to normal |

Depths: nasolabial crease 1–2 mm (elder 3–5 mm), forehead lines 0.3–0.6 mm, pores 0.05–0.15 mm. Never sculpt pores deeper than 0.2 mm: at game distance they turn to noise.

## Headless bpy (via `blender_execute_blender_code`)

```python
import bpy
ob = bpy.data.objects["Head"]
mr = ob.modifiers.new("Multires", "MULTIRES")
for _ in range(4):
    with bpy.context.temp_override(object=ob, active_object=ob):
        bpy.ops.object.multires_subdivide(modifier="Multires", mode="CATMULL_CLARK")
# tertiary pores as displacement, then bake instead of hand strokes
tex = bpy.data.textures.new("pores", "VORONOI"); tex.noise_scale = 0.0012
d = ob.modifiers.new("Pores", "DISPLACE"); d.texture = tex; d.strength = 0.00008; d.texture_coords = "OBJECT"
```

In Forge, the same chain is `sculpt_hd(id, levels=3, detail=pores)`, then `bake(id, from_high=true)`.

## Mask tertiary detail

Concentrate pores on the nose, cheeks and chin. Keep them faint on the lids and lips. Use none inside the lip vermilion: lips get vertical lip lines (0.1 mm, 1 mm apart).

## Done when

A grey matcap `blender_get_viewport_screenshot` at 3 m shows the primary forms only, and at 0.3 m shows pores. The baked normal at 2048 px shows no stepping.

---
MIT, uefn-ducky; own words, common sculpting practice.
