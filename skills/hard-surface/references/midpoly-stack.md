# Mid-poly stack presets

One modifier stack per finish, sized from the object. Run through `blender_execute_blender_code`. Unwrap UVs **before** adding the stack: the bevel keeps them.

| Preset | Stack (order matters) | Use |
|---|---|---|
| `midpoly` | Bevel (1 % of largest dimension, 3 seg, angle 30°, clamp overlap, harden normals) → Weighted Normal (Face Area, keep sharp) | game props (default) |
| `subd` | Bevel (0.5 %, 2 seg: support loops) → Subdivision 2 | smooth hero shapes |
| `render` | Bevel (1 %, 5 seg, harden) → Weighted Normal | close-up stills |

Full order on a real asset: Mirror → Booleans → Bevel → Weighted Normal → Triangulate (only at export).

```python
import bpy, math

def hs_stack(ob, preset="midpoly", weight_angle=None):
    """Replace the HS_ modifiers on ob with a preset stack. weight_angle: bevel only edges sharper than it (deg)."""
    for m in [m for m in ob.modifiers if m.name.startswith("HS_")]:
        ob.modifiers.remove(m)
    w = max(ob.dimensions) * (0.005 if preset == "subd" else 0.01)
    b = ob.modifiers.new("HS_Bevel", "BEVEL")
    b.width, b.segments = w, {"midpoly": 3, "subd": 2, "render": 5}[preset]
    b.limit_method, b.angle_limit = "ANGLE", math.radians(weight_angle or 30)
    b.use_clamp_overlap = True
    b.harden_normals = preset != "subd"
    if preset == "subd":
        s = ob.modifiers.new("HS_Subd", "SUBSURF")
        s.levels = s.render_levels = 2
    else:
        n = ob.modifiers.new("HS_WeightedNormal", "WEIGHTED_NORMAL")
        n.mode, n.keep_sharp = "FACE_AREA", True
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    tris = sum(len(p.vertices) - 2 for p in ev.data.polygons)
    return f"{preset}: bevel {w:.4f} m {b.segments} seg -> {tris} tris"

bpy.ops.mesh.primitive_cube_add(size=2)
print(hs_stack(bpy.context.active_object, "midpoly"))
```

**Done when:** a 3/4 viewport render shows a thin highlight on every hard edge and flat faces without shading streaks; the printed tris fit the budget (prop 0.3-3k, hero 5-20k).

Bevel by angle (`weight_angle=45`) leaves soft edges alone without painting bevel weights. Segments: bolts 6-8, handles 12-16, barrels 24-32.

---
Adapted from Blender Agent Skills (hardsurface-modeling) by EL4CTEO, MIT licence. Same presets as Forge `modifiers(stack=...)`.
