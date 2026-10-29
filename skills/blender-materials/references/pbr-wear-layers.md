---
description: "Procedural wear layers in Principled node graphs with exact values: edge wear from Pointiness, cavity dirt from AO, stretched-noise scratches, painted metal, wet (albedo darkens up to 55 % by porosity, roughness 0.08, coat) and snow on up-facing faces, plus vertex-colour masks R wear / G dirt / B wet"
metadata:
  label: "PBR Wear Layers"
---

# PBR Wear Layers

Layers stack on one running colour / roughness / metallic. Pointiness and AO nodes are Cycles-only: bake them (`texture-workflow` → `bake-maps-cage`) before export.

| Layer | Mask | Mix into |
|---|---|---|
| edge wear | Geometry.Pointiness → ColorRamp 0.50 → 0.52-0.82 (width) × Noise(scale 8) ramp 0.35-0.65 × amount 0.7 | colour → 0.55 grey (bare metal 0.6), roughness → 0.45, metallic → 1 if metal underneath |
| dirt | 1 − AO(distance 0.15 m, 8 samples) → ramp 0.2-0.8 × Noise(4) ramp 0.3-0.7 × 0.6 | colour → 0.08, 0.06, 0.04; roughness → 0.9; metallic → 0 |
| scratches | Noise(scale 30, mapping Y × 20) → ramp 0.52-0.56 × 0.5 | colour → 0.7; roughness → 0.25; bump −0.3 |
| wet | constant amount (or vertex colour B) | colour × (1 − 0.55 · porosity · amount); roughness → 0.08; Coat Weight = amount, Coat Roughness 0.05 |
| snow | Geometry.Normal → Separate XYZ.Z → ramp (up − 0.1, up + 0.1), up 0.6 × amount 0.8 | colour → 0.85, 0.86, 0.87; roughness → 0.6; metallic → 0 |

```python
import bpy

def edge_wear(mat, amount=0.7, width=0.5, wear=(0.55, 0.55, 0.58, 1)):
    t = mat.node_tree; N = t.nodes.new; L = t.links.new
    b = next(n for n in t.nodes if n.type == "BSDF_PRINCIPLED")
    geo = N("ShaderNodeNewGeometry")
    ramp = N("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].position = 0.5
    ramp.color_ramp.elements[1].position = 0.52 + 0.3 * (1 - width)
    L(geo.outputs["Pointiness"], ramp.inputs[0])
    noise = N("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 8
    br = N("ShaderNodeValToRGB"); br.color_ramp.elements[0].position, br.color_ramp.elements[1].position = 0.35, 0.65
    L(noise.outputs["Fac"], br.inputs[0])
    m1 = N("ShaderNodeMath"); m1.operation = "MULTIPLY"; L(ramp.outputs[0], m1.inputs[0]); L(br.outputs[0], m1.inputs[1])
    fac = N("ShaderNodeMath"); fac.operation = "MULTIPLY"; fac.use_clamp = True
    L(m1.outputs[0], fac.inputs[0]); fac.inputs[1].default_value = amount
    mix = N("ShaderNodeMix"); mix.data_type = "RGBA"
    old = b.inputs["Base Color"]
    if old.is_linked: L(old.links[0].from_socket, mix.inputs[6])
    else: mix.inputs[6].default_value = old.default_value
    mix.inputs[7].default_value = wear
    L(fac.outputs[0], mix.inputs[0]); L(mix.outputs[2], b.inputs["Base Color"])
    return fac  # reuse as the mask for roughness / metallic mixes

def snow(mat, up=0.6, amount=0.8):
    t = mat.node_tree; N = t.nodes.new; L = t.links.new
    b = next(n for n in t.nodes if n.type == "BSDF_PRINCIPLED")
    z = N("ShaderNodeSeparateXYZ"); L(N("ShaderNodeNewGeometry").outputs["Normal"], z.inputs[0])
    r = N("ShaderNodeValToRGB"); r.color_ramp.elements[0].position, r.color_ramp.elements[1].position = up - 0.1, up + 0.1
    L(z.outputs["Z"], r.inputs[0])
    f = N("ShaderNodeMath"); f.operation = "MULTIPLY"; L(r.outputs[0], f.inputs[0]); f.inputs[1].default_value = amount
    mix = N("ShaderNodeMix"); mix.data_type = "RGBA"; mix.inputs[7].default_value = (0.85, 0.86, 0.87, 1)
    mix.inputs[6].default_value = b.inputs["Base Color"].default_value
    L(f.outputs[0], mix.inputs[0]); L(mix.outputs[2], b.inputs["Base Color"])
```

- **painted_metal:** base paint Metallic 0, roughness 0.45; edge wear colour 0.6 grey with its mask also driving Metallic 0 → 1; scratches 0.3; dirt 0.4.
- **Vertex-colour masks** for game export: paint R = wear, G = dirt, B = wet on a `Color Attribute` node and use the channel as the layer's mask instead of Pointiness/AO. They survive FBX/glTF and cost no textures.
- Particle rain/snow belongs to the engine (UEFN Niagara); keep only the surface layers here.

Adapted from Blender Agent Skills by EL4CTEO (pbr-materials, weather; MIT). Same layers as Forge `material` layers `edge_wear dirt scratches wet snow`.
