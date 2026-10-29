---
description: "Measured PBR presets (gold, iron, aluminium, silver, titanium, copper, chrome, painted metal, gloss, plastic, rubber, glass, skin) as linear Principled values, category presets, and a bpy lint that flags metallic between 0 and 1, albedo outside sRGB 30-240 (metals 180+) and maps in the wrong colour space"
metadata:
  label: "PBR Presets and Lint"
---

# PBR Presets and Lint

Principled BSDF Base Color is **linear**. Metals: Base Color = F0 tint, Metallic 1. Everything else: Metallic 0.

| Preset | Base Color (linear) | Metallic | Roughness | Extra |
|---|---|---|---|---|
| gold | 1.00, 0.77, 0.34 | 1 | 0.2 | |
| copper | 0.95, 0.64, 0.54 | 1 | 0.28 | |
| iron | 0.56, 0.57, 0.58 | 1 | 0.5 | noise → roughness ±0.1 |
| aluminium | 0.91, 0.92, 0.92 | 1 | 0.3 | |
| silver | 0.97, 0.96, 0.91 | 1 | 0.15 | |
| titanium | 0.54, 0.50, 0.45 | 1 | 0.35 | |
| chrome | 0.95, 0.95, 0.97 | 1 | 0.03 | |
| painted_metal | paint colour | 0 | 0.45 | edge wear shows metal 0.6 grey, Metallic 1 (`pbr-wear-layers`) |
| gloss (car paint, product) | any | 0 | 0.02 | Coat Weight 1, Coat Roughness 0.02 |
| plastic | any, ≤ 0.87 | 0 | 0.3-0.4 | |
| rubber | 0.04 | 0 | 0.9 | |
| glass | 0.87 | 0 | 0.0 | Transmission Weight 1, IOR 1.5 |
| skin | 0.86, 0.65, 0.55 (light) | 0 | 0.45 | Subsurface Weight 0.4, Radius 1, 0.35, 0.2 |
| snow | 0.87 | 0 | 0.7 | |

Category presets: ask for "metal" → worn steel, "wood" → oak, "stone" → granite, "fabric" → cotton, "skin" → light skin, "plastic" → white plastic, "glass" → clear glass.

## Lint

```python
import bpy

def srgb(c):
    c = max(0.0, c)
    return 255 * (12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055)

def lint(mat):
    out = []
    b = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    m = b.inputs["Metallic"]
    if not m.is_linked and 0.05 < m.default_value < 0.95:
        out.append(f"metallic {m.default_value:.2f}: use 0 or 1, mask the mix")
    col = b.inputs["Base Color"]
    if not col.is_linked:
        bright = max(srgb(c) for c in col.default_value[:3])
        if m.default_value >= 0.5 and bright < 180:
            out.append(f"metal albedo sRGB {bright:.0f} < 180")
        if m.default_value < 0.5 and not 30 <= bright <= 240:
            out.append(f"albedo sRGB {bright:.0f} outside 30-240")
    for n in mat.node_tree.nodes:  # data maps must be Non-Color, colour maps sRGB
        if n.type == "TEX_IMAGE" and n.image and n.outputs["Color"].links:
            to = n.outputs["Color"].links[0].to_socket.name
            data = to not in ("Base Color", "Emission Color", "Color")
            if data != (n.image.colorspace_settings.name == "Non-Color"):
                out.append(f"{n.image.name}: colour space {n.image.colorspace_settings.name} feeds {to}")
    return out

for mat in bpy.data.materials:
    if mat.node_tree:
        print(mat.name, lint(mat) or "ok")
```

Done when: every material prints `ok`, and a `lookdev-light-presets` studio render reads as the material.

Adapted from Blender Agent Skills by EL4CTEO (pbr-materials; MIT). Metal F0 from physicallybased.info. Same presets and lint as Forge `material`.
