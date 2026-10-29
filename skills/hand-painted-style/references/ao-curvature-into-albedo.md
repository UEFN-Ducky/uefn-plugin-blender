---
description: "Hand-painted albedo from bakes: bake AO and curvature, then paint them into the base colour (AO multiply 0.4-0.6, curvature edge highlight 0.25-0.35, gradient lighter toward the top, warm rim) so the texture holds its form under flat game light"
metadata:
  label: "AO and Curvature into Albedo"
---

# AO and Curvature into Albedo

Hand-painted is the one style that **does** put light in the albedo. Bake first (`texture-workflow` → `bake-maps-cage`: AO 16 samples, curvature via Pointiness), then mix:

| Layer | Blend | Amount |
|---|---|---|
| base flat colours | — | palette of 3-5 hues per material |
| top-down gradient (Geometry.Position Z or Normal Z) | overlay, lighter up, darker down | 0.2-0.3 |
| AO | multiply, tinted toward the shadow hue (not black) | 0.4-0.6 |
| curvature convex | screen / add, highlight hue | 0.25-0.35 |
| curvature concave | multiply, shadow hue | 0.2 |
| rim (Layer Weight Facing) | add warm or sky hue | 0.1-0.15 |

```python
import bpy
# after baking T_X_AO and T_X_CRV into images ao, crv; base is the flat colour image
def paint_light(mat, ao, crv, shadow=(0.25, 0.18, 0.3, 1), light=(1.0, 0.92, 0.75, 1)):
    t = mat.node_tree; N = t.nodes.new; L = t.links.new
    b = next(n for n in t.nodes if n.type == "BSDF_PRINCIPLED")
    base = b.inputs["Base Color"].links[0].from_socket
    a = N("ShaderNodeTexImage"); a.image = ao; a.image.colorspace_settings.name = "Non-Color"
    c = N("ShaderNodeTexImage"); c.image = crv; c.image.colorspace_settings.name = "Non-Color"
    inv = N("ShaderNodeInvert"); L(a.outputs[0], inv.inputs[1])
    m1 = N("ShaderNodeMix"); m1.data_type = "RGBA"; m1.blend_type = "MULTIPLY"
    L(base, m1.inputs[6]); m1.inputs[7].default_value = shadow; L(inv.outputs[0], m1.inputs[0])
    ramp = N("ShaderNodeMapRange"); ramp.inputs["From Min"].default_value = 0.55; L(c.outputs[0], ramp.inputs[0])
    m2 = N("ShaderNodeMix"); m2.data_type = "RGBA"; m2.blend_type = "SCREEN"
    L(m1.outputs[2], m2.inputs[6]); m2.inputs[7].default_value = light
    f = N("ShaderNodeMath"); f.operation = "MULTIPLY"; L(ramp.outputs[0], f.inputs[0]); f.inputs[1].default_value = 0.3
    L(f.outputs[0], m2.inputs[0]); L(m2.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.8; b.inputs["Metallic"].default_value = 0
```

Then bake the result to one Base Color image (Emit bake of Base Color) and ship that single texture: roughness constant 0.7-0.9, no normal map unless the form needs it.

Done when: a `neutral` (even, flat) light still shows the form from the albedo alone.

Adapted from Blender Agent Skills by EL4CTEO (baking, stylized materials; MIT). Same idea as Forge `paint_strokes(ao, rim)` and `paint_bake`.
