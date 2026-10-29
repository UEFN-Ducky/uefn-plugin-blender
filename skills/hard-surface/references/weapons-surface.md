---
description: "Gun hard-surface stack (blockout, booleans, chamfer, weighted normals, mid-poly vs bake), melee edge bevels and grinds, and wear masks for metal, polymer, wood and grip materials"
metadata:
  label: "Weapon surfaces and wear"
---

# Weapon surfaces: stack, edges, wear

## Gun hard-surface stack

Order matters: Blockout → Booleans (live) → Bevel → Weighted Normal → Triangulate (export only). Unwrap before the bevel, it keeps the UVs.

| step | realistic | stylized |
|---|---|---|
| bevel width | 1.5-2 mm, 2-3 segments, limit by angle 30°, harden normals | 4-6 mm, 3 segments |
| weighted normal | Face Area, Keep Sharp, weight 50 | same |
| smallest modeled detail | 2 mm (FPS), 5 mm (TPS); finer goes to the normal map | 5 mm |
| panel / seam lines | boolean slot 0.8-1.2 mm wide, 0.5 mm deep | 2 mm |
| vents, M-LOK slots | boolean array; on curved parts add support loops first | |

Two ways to ship: **mid-poly** (the stack above is the final mesh, custom normals, no bake; TPS, pickups, stylized) or **high to low** (subd high poly with 3-loop support edges, bake normal + AO + curvature onto a 1-1.2 mm chamfered low poly; FPS hero). See `midpoly-stack.md` for the preset code and `../../asset-optimization/` for LODs.

```python
import bpy
ob = bpy.context.active_object
b = ob.modifiers.new("HS_Bevel", "BEVEL")
b.width, b.segments, b.limit_method, b.angle_limit = 0.0018, 3, "ANGLE", 0.5236
b.harden_normals, b.use_clamp_overlap = True, True
w = ob.modifiers.new("HS_WNormal", "WEIGHTED_NORMAL")
w.keep_sharp, w.weight = True, 50
```

## Melee edge bevels

A cutting edge is never zero width: give it a tiny bevel so it catches a highlight line.

| zone | bevel | segments |
|---|---|---|
| cutting edge | 0.2-0.5 mm | 1 |
| spine / flat-to-spine | 1-2 mm | 2 |
| guard, pommel, bolster | 2-3 mm | 2-3 |
| haft / handle corners | 3-5 mm (or 8-sided section) | 2 |

Grinds (cross-section): flat (straight taper, knives, cheap swords), hollow (concave, razors), convex / hamaguri (katana), diamond (central ridge, arming swords), fuller (groove, 1/3 blade width, 60-80 % blade length). Model the grind as a second loop 3-8 mm in from the edge; keep it crisp with Mark Sharp. Blade tip: taper thickness to 0.1-0.2 cm over the last 10 %.

## Wear masks

Wear goes in the material (texture), never in the mesh. Base values (linear):

| material | base colour | metallic | roughness | wear |
|---|---|---|---|---|
| parkerized / anodized steel | 0.04-0.05 | 1.0 | 0.45-0.6 | convex edges → bare steel 0.55-0.65, roughness 0.25-0.35 |
| polished blade steel | 0.6-0.75 | 1.0 | 0.2-0.42 | fine scratches along the blade, oxidation in the fuller |
| polymer | 0.03-0.04 | 0.0 | 0.6-0.7 | no bright edges: high-touch areas (grip, mag base, charging handle) get smoother 0.4-0.45 and 0.01-0.02 lighter |
| stippled grip | 0.02 | 0.0 | 0.85-0.9 | stipple as a normal map, 1-1.5 mm dots |
| wood | 0.28, 0.13, 0.05 | 0.0 | 0.5-0.6 | lighter, smoother spots on hand contact; darker oil in the grain |
| glow (sci-fi) | cyan / orange | 0.0 | 0.3 | none; emission 3-8 in Blender |

Edge-wear mask: convex curvature x noise. Pointiness only works in Cycles, so bake the mask (or a curvature map) before export.

```python
import bpy
mat = bpy.data.materials["Weapon_Metal"]; nt = mat.node_tree; N = nt.nodes.new
bsdf = nt.nodes["Principled BSDF"]
geo, ramp, noise, mul = N("ShaderNodeNewGeometry"), N("ShaderNodeValToRGB"), N("ShaderNodeTexNoise"), N("ShaderNodeMath")
ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = 0.52, 0.56  # tune per mesh density
noise.inputs["Scale"].default_value, mul.operation = 60.0, "MULTIPLY"
nt.links.new(geo.outputs["Pointiness"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], mul.inputs[0]); nt.links.new(noise.outputs["Fac"], mul.inputs[1])
mix = N("ShaderNodeMix"); mix.data_type = "RGBA"
mix.inputs[6].default_value, mix.inputs[7].default_value = (0.045, 0.047, 0.05, 1), (0.6, 0.6, 0.58, 1)
nt.links.new(mul.outputs[0], mix.inputs[0]); nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
```

Done when: a three-quarter render shows a thin highlight on every chamfer, bright wear only on convex metal edges (never on polymer), and the blade edge reads as a light line.

## Forge path

`weapon` already applies the chamfer + weighted normals and the slots above; add wear with `material` layers `edge_wear`, `scratches`.

---
The bevel + weighted-normal stack and mid-poly vs bake split are adapted from Blender Agent Skills (hardsurface-modeling, baking, pbr-materials) by EL4CTEO, MIT licence. Material values are typical physically based ranges.
