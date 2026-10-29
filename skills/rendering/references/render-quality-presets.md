---
description: "Render quality presets with exact samples: preview (Eevee 16), final (Eevee 64 / Cycles 256 + denoise), product (Eevee 128 / Cycles 512, 2048 px), and bake renders (Cycles 1 sample for value maps, 16 for AO), with the view transform per use"
metadata:
  label: "Render Quality Presets"
---

# Render Quality Presets

| Preset | Engine, samples | Size | Transform | Use |
|---|---|---|---|---|
| preview | Eevee, `taa_render_samples = 16` | 640×480 | AgX | every iteration still |
| final | Eevee 64, or Cycles 256 + OpenImageDenoise | 1920×1080 | AgX | review, portfolio |
| product | Eevee 128, or Cycles 512 + denoise | 2048×2048 | Khronos PBR Neutral or AgX | store art, thumbnails |
| bake (value maps, normal) | Cycles 1 sample, denoise off, adaptive off | map size | n/a | exact values |
| bake (AO, thickness) | Cycles 16 samples | map size | n/a | |

```python
import bpy

def quality(preset="preview"):
    s = bpy.context.scene
    eevee = {"preview": 16, "final": 64, "product": 128}[preset]
    s.render.engine = "BLENDER_EEVEE"; s.eevee.taa_render_samples = eevee
    s.render.resolution_x, s.render.resolution_y = {"preview": (640, 480), "final": (1920, 1080), "product": (2048, 2048)}[preset]
    s.view_settings.view_transform = "Khronos PBR Neutral" if preset == "product" else "AgX"
```

- Bake GPU only from 1024 px up; smaller bakes are faster on CPU (kernel load costs seconds).
- Pair each still with a light preset from `lighting` → `lookdev-light-presets`.

Adapted from Blender Agent Skills by EL4CTEO (rendering; MIT). Same levels as Forge `light(quality=preview|final|product)`.
