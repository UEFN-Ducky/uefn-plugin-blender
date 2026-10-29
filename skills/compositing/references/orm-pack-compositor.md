---
description: "Pack baked AO, roughness and metallic into one ORM texture (R AO, G rough, B metal) and flip a normal map's green channel with compositor or numpy, Non-Color in and out, plus a side-by-side compare of light-preset stills"
metadata:
  label: "ORM Pack and Map Compositing"
---

# ORM Pack and Map Compositing

Engines read one ORM texture: **R = AO, G = roughness, B = metallic**, linear (Non-Color). A missing AO is 1.0, a missing metallic 0.0.

```python
import bpy, numpy as np

def px(img):
    a = np.empty(len(img.pixels), np.float32); img.pixels.foreach_get(a)
    return a.reshape(-1, 4)

def pack_orm(ao, rough, metal, name="T_X_ORM", path="//T_X_ORM.png"):
    size = rough.size
    out = bpy.data.images.new(name, *size, alpha=False)
    out.colorspace_settings.name = "Non-Color"
    o = np.ones((size[0] * size[1], 4), np.float32)
    o[:, 0] = px(ao)[:, 0] if ao else 1.0
    o[:, 1] = px(rough)[:, 0]
    o[:, 2] = px(metal)[:, 0] if metal else 0.0
    out.pixels.foreach_set(o.ravel()); out.filepath_raw = path; out.file_format = "PNG"; out.save()
    return out

def flip_green(img):  # OpenGL <-> DirectX normal
    a = px(img); a[:, 1] = 1.0 - a[:, 1]; img.pixels.foreach_set(a.ravel()); img.update()
```

Same sizes in, or scale the smaller maps first (`img.scale(w, h)`). Compositor alternative: Image nodes → Separate Color (RGB) → Combine Color (AO.R, Rough.R, Metal.R) → File Output with Color Management "Override", Non-Color.

**Compare stills:** render the same camera under `studio`, `dramatic` and `neutral` (`lighting` → `lookdev-light-presets`), then place them side by side in one image (numpy `np.hstack`) for a single review look.

Adapted from Blender Agent Skills by EL4CTEO (baking, pbr-materials; MIT). Same packing as Forge `bake(maps=["orm"])` and `material(textures=)`.
