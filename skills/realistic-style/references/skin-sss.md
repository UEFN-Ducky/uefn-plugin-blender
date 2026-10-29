---
description: "Realistic skin shader: SSS radius per channel, albedo ranges by tone, roughness breakup (oily T-zone vs cheeks), pore normal, lips and eye-area values, bpy node setup"
metadata:
  label: "Skin shader (SSS)"
---

# Skin shader

| Input | Value | Why |
|---|---|---|
| Subsurface Weight | 1.0 | skin is fully translucent at the mm scale |
| Subsurface Radius | **R 1.0, G 0.35, B 0.2 cm** (scale 0.01 in a metre scene) | red scatters furthest: soft red shadow edges |
| Subsurface method | Random Walk (Skin) | handles thin ears and nostrils |
| Albedo (linear) | light (0.68, 0.45, 0.36) … deep (0.13, 0.065, 0.04) | sRGB 50–215; never saturated orange |
| Roughness | 0.45–0.55 base; T-zone (forehead, nose, chin) **0.30–0.35**; cheeks 0.55–0.6 | oily vs dry zones; one flat value reads as plastic |
| Specular IOR level | 0.5 (IOR 1.4) | skin F0 ≈ 0.028 |
| Pore normal | 0.05–0.15 mm detail baked from the sculpt; bump strength 0.2–0.4 | breaks the highlight into a sheen |
| Colour variation | +6% red over the cheeks, nose and ears; slightly blue-grey under the eyes and at the jaw (stubble) | blood flow zones |
| Lips | albedo × (1, 0.62, 0.62), rough 0.35–0.4, vertical lip-line bump | |
| Eye area | lid roughness 0.4; caruncle 0.15 (wet) | |

## bpy (via `blender_execute_blender_code`)

```python
import bpy
m = bpy.data.materials.new("M_Skin"); m.use_nodes = True
nt = m.node_tree; b = nt.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.58, 0.38, 0.30, 1)
b.inputs["Subsurface Weight"].default_value = 1.0
b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
b.inputs["Subsurface Scale"].default_value = 0.01
b.subsurface_method = "RANDOM_WALK_SKIN"
# roughness: T-zone mask (painted or a vertex colour "tzone", 1 = oily) -> 0.32..0.56
attr = nt.nodes.new("ShaderNodeVertexColor"); attr.layer_name = "tzone"
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["To Min"].default_value = 0.56; mr.inputs["To Max"].default_value = 0.32
noise = nt.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 40
add = nt.nodes.new("ShaderNodeMath"); add.operation = "MULTIPLY_ADD"; add.inputs[1].default_value = 0.16; add.inputs[2].default_value = -0.08
nt.links.new(attr.outputs["Color"], mr.inputs["Value"])
nt.links.new(noise.outputs["Fac"], add.inputs[0])
fin = nt.nodes.new("ShaderNodeMath"); fin.operation = "ADD"; fin.use_clamp = True
nt.links.new(mr.outputs["Result"], fin.inputs[0]); nt.links.new(add.outputs["Value"], fin.inputs[1])
nt.links.new(fin.outputs["Value"], b.inputs["Roughness"])
```

For UE/UEFN, bake the roughness into ORM G and use the engine's Subsurface Profile. The Blender SSS radius maps to the profile's Mean Free Path (same cm values).

**Forge**: `forge_hq op=head` writes this as a layer spec: base, a T-zone roughness map, noise, a pore bump and `sss` radius [1, 0.35, 0.2] scale 0.01.

## Lighting check

Light with one soft key at 45° plus a dim fill. Look for these:

- The shadow terminator turns warm red, not grey.
- The ears glow red with a back light.
- The highlight is broken into a sheen, not a mirror spot.

## Don't

- Don't use a radius above about 1.5 cm on red: it reads as wax or jade.
- Don't use pure-white specular highlights on the lips. Keep the lips rougher than the T-zone.
- Don't use photo albedo with baked lighting. Neutralise shadows first (see `scan-cleanup.md`).

---
Values are published measurement averages (skin scattering, IOR) in our own words. MIT, uefn-ducky.
