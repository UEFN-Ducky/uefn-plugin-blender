---
description: "Car materials in Blender 5.x Principled BSDF: car paint with metallic flakes and clearcoat 1.0 / roughness 0.03, glass, chrome, rubber, tire, plastic trim, lights; UE / UEFN equivalents"
metadata:
  label: "Car paint, glass, chrome, rubber"
---

# Car paint, glass, chrome, rubber

## Values (Principled BSDF)

| Slot | Base colour (linear) | Metallic | Roughness | Extra |
|---|---|---|---|---|
| paint | e.g. 0.55, 0.03, 0.04 | 0.25-0.6 (solid 0, metallic 0.6) | 0.3 | **Coat Weight 1.0, Coat Roughness 0.03**, Coat IOR 1.5, flakes in the normal |
| chrome | 0.95, 0.95, 0.96 | 1.0 | 0.05 | — |
| alloy rim | 0.7, 0.7, 0.72 | 1.0 | 0.2-0.25 | — |
| brake disc | 0.42, 0.42, 0.43 | 1.0 | 0.35-0.45 | — |
| rubber / tire | 0.025 | 0 | 0.85-0.9 | sidewall slightly glossier (0.7) |
| trim plastic | 0.035 | 0 | 0.55 | — |
| glass | 0.04, 0.06, 0.07 | 0 | 0.02 | Alpha 0.35 (or Transmission 1.0), IOR 1.5 |
| headlight lens | white | 0 | 0.02 | Transmission 1.0 |
| tail lens | 0.45, 0.01, 0.01 | 0 | 0.05 | Alpha 0.7 |
| DRL / emissive | 0.9 | 0 | 0.2 | Emission 1, 0.95, 0.85 × 6 (tail red × 4) |
| leather | 0.09, 0.065, 0.05 | 0 | 0.6 | Sheen 0.2 |

## Car paint with flakes

```python
import bpy
mat = bpy.data.materials.new("M_CarPaint")
nt = mat.node_tree
bsdf = nt.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.55, 0.03, 0.04, 1)
bsdf.inputs["Metallic"].default_value = 0.6
bsdf.inputs["Roughness"].default_value = 0.3
bsdf.inputs["Coat Weight"].default_value = 1.0
bsdf.inputs["Coat Roughness"].default_value = 0.03
bsdf.inputs["Coat IOR"].default_value = 1.5
noise = nt.nodes.new("ShaderNodeTexVoronoi")      # metallic flakes
noise.inputs["Scale"].default_value = 4000.0       # ~0.25 mm cells at 1 m
bump = nt.nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.08
nt.links.new(noise.outputs["Distance"], bump.inputs["Height"])
nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])   # flakes under the coat; the coat stays smooth
```

The flake bump goes into **Normal**, not **Coat Normal**, so the clearcoat reflection stays mirror-clean. Bake flakes into a tiling normal map for UE (`texture_bake`).

## UE / UEFN

UE materials: Shading Model **Clear Coat**: ClearCoat 1.0, ClearCoatRoughness 0.03, Metallic 0.6, Roughness 0.3, plus a tiling flake normal. UEFN Material Instance: use the Clear Coat parent if your project has one, else Metallic 0.6 / Roughness 0.25. Glass: Translucent, Surface TranslucencyVolume, Opacity 0.35. Lights: Emissive Color × 6-20 (bloom). One material slot per type, shared by every car, so a single paint instance recolours the fleet.

**Done when:** a 3/4 studio render shows a sharp coat highlight over a softer metallic base, the glass shows the seats, and the DRL glows.

Forge: car parts already use the shared ids `mcar_paint` (with clearcoat 1.0 / 0.03), `mcar_chrome`, `mcar_rubber`, `mcar_glass`, `mcar_plastic`, `mcar_emissive`…

---
Values from Blender 5.x Principled BSDF and UE Clear Coat docs; layering advice adapted from Blender Agent Skills (pbr-materials) by EL4CTEO, MIT licence.
