---
description: "Wire a downloaded texture set (Poly Haven, ambientCG, Substance, UE T_X_BC) by file-name suffix into a Principled material: colour spaces, ORM split, separate AO/rough/metal packed to ORM, OpenGL vs DirectX normal flip, height skipped"
metadata:
  label: "Texture Set Wiring"
---

# Texture Set Wiring

Read the **last** token of the file name that names a map (so `metal_plate_diff_2k` is base colour, not metallic).

| Slot | Tokens | Colour space |
|---|---|---|
| base colour | diff, diffuse, albedo, basecolor, color, col, bc, d | sRGB |
| normal | nor_gl, normalgl, normal, nrm, normaldx, `_N` | Non-Color; `dx`/`normaldx`/UE `_N` = DirectX |
| roughness | rough, roughness | Non-Color |
| metallic | metal, metalness, metallic | Non-Color |
| AO | ao, ambientocclusion, occlusion | Non-Color (pack into ORM R; never multiply into albedo for PBR) |
| ORM | arm (Poly Haven), orm, occlusionroughnessmetallic | Non-Color: R AO, G rough, B metal |
| emissive / opacity | emissive, emission / opacity, alpha | sRGB / Non-Color |
| height | disp, displacement, height | skip for games (bake it into the normal) |

```python
import bpy, re
from pathlib import Path
TOK = {"orm": {"orm", "arm"}, "normal": {"normal", "normalgl", "normaldx", "nor", "nrm", "n"},
       "rough": {"rough", "roughness"}, "metal": {"metal", "metalness", "metallic"},
       "color": {"diff", "diffuse", "albedo", "basecolor", "color", "col", "bc", "d"}}

def slot(stem):
    toks = [t for t in re.split(r"[_\-. ]+", stem.lower()) if t]
    for t in reversed(toks[1:]):
        for s, names in TOK.items():
            if t in names:
                return s, ("dx" in toks or "normaldx" in toks or toks[-1] == "n")
    return None, False

def wire(mat, folder):
    t = mat.node_tree; N = t.nodes.new; L = t.links.new
    b = next(n for n in t.nodes if n.type == "BSDF_PRINCIPLED")
    for f in sorted(Path(folder).glob("*.*")):
        s, dx = slot(f.stem)
        if not s: continue
        tex = N("ShaderNodeTexImage"); tex.image = bpy.data.images.load(str(f), check_existing=True)
        if s != "color": tex.image.colorspace_settings.name = "Non-Color"
        if s == "color": L(tex.outputs["Color"], b.inputs["Base Color"])
        elif s == "rough": L(tex.outputs["Color"], b.inputs["Roughness"])
        elif s == "metal": L(tex.outputs["Color"], b.inputs["Metallic"])
        elif s == "orm":
            sep = N("ShaderNodeSeparateColor"); L(tex.outputs["Color"], sep.inputs[0])
            L(sep.outputs[1], b.inputs["Roughness"]); L(sep.outputs[2], b.inputs["Metallic"])
        elif s == "normal":
            src = tex.outputs["Color"]
            if dx:  # Blender wants OpenGL: G = 1 - G
                sep = N("ShaderNodeSeparateColor"); comb = N("ShaderNodeCombineColor"); inv = N("ShaderNodeMath")
                inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1
                L(src, sep.inputs[0]); L(sep.outputs[1], inv.inputs[1])
                L(sep.outputs[0], comb.inputs[0]); L(inv.outputs[0], comb.inputs[1]); L(sep.outputs[2], comb.inputs[2])
                src = comb.outputs[0]
            nm = N("ShaderNodeNormalMap"); L(src, nm.inputs["Color"]); L(nm.outputs[0], b.inputs["Normal"])
```

- Separate AO + rough + metal for an engine: pack them with `orm-packing` (R AO, G rough, B metal; missing AO = 255, missing metal = 0).
- Engine normal convention: Unreal / UEFN = DirectX (flip green from GL sources), Unity, Godot, glTF = OpenGL.
- Check with `blender-materials` → `pbr-presets-and-lint`: no "colour space" lines.

Adapted from Blender Agent Skills by EL4CTEO (pbr-materials texture-set import; MIT). Same rules as Forge `material(textures=<folder>)`.
