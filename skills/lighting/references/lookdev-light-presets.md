---
description: "One-word look-dev light presets in bpy (studio, product, dramatic, soft, neutral) placed relative to the camera and sized to the object, plus outdoor noon / golden / night suns, with exact angles, energies and backdrop greys"
metadata:
  label: "Look-dev Light Presets"
---

# Look-dev Light Presets

Azimuth is measured from the camera (0 = behind the camera, + = camera left). Suns with an angular size stand in for area lights about the object's size, so energy (W/m²) does not depend on distance.

| Preset | Key (az, el, W/m², softness) | Fill | Rim | World grey, strength | Floor |
|---|---|---|---|---|---|
| studio | 45°, 35°, 2.2, 25° | −50°, 15°, 0.7 (⅓), 40° | 160°, 45°, 1.4, 15° | 0.18, 0.4 | 0.18 |
| product | 35°, 50°, 2.0, 45° | −60°, 20°, 1.0 (½), 60° | 180°, 40°, 1.0, 20° | 0.8, 0.6 | 0.8 |
| dramatic | 80°, 25°, 3.0, 6° | −80°, 10°, 0.15 | 200°, 30°, 2.5, 8° | 0.02, 0.1 | 0.05 |
| soft | 20°, 60°, 1.6, 60° | −40°, 30°, 0.9, 60° | none | 0.35, 0.7 | 0.4 |
| neutral | none | none | none | 1.0, 1.0 (even white) | 0.5 |

| env | Sun elevation, energy, colour | Sky colour, strength | Exposure |
|---|---|---|---|
| noon | 60°, 4.0, (1, 0.97, 0.92) | (0.45, 0.6, 0.9), 1.0 | 0 |
| golden | 8°, 2.5, (1, 0.62, 0.35) | (0.9, 0.55, 0.35), 0.5 | +0.3 |
| night | 35°, 0.35, (0.55, 0.65, 1) | (0.02, 0.03, 0.08), 0.3 | +1.5 |

```python
import bpy, math
from mathutils import Vector

PRESETS = {"studio": [("key", 45, 35, 2.2, 25), ("fill", -50, 15, 0.7, 40), ("rim", 160, 45, 1.4, 15)],
           "product": [("key", 35, 50, 2.0, 45), ("fill", -60, 20, 1.0, 60), ("rim", 180, 40, 1.0, 20)],
           "dramatic": [("key", 80, 25, 3.0, 6), ("fill", -80, 10, 0.15, 30), ("rim", 200, 30, 2.5, 8)],
           "soft": [("key", 20, 60, 1.6, 60), ("fill", -40, 30, 0.9, 60)], "neutral": []}

def light(preset, cam, target=Vector((0, 0, 0))):
    for o in [o for o in bpy.data.objects if o.name.startswith("LGT_")]:
        bpy.data.objects.remove(o)
    d = cam.location - target
    base = math.atan2(d.y, d.x)
    for name, az, el, energy, soft in PRESETS[preset]:
        a, e = base + math.radians(az), math.radians(el)
        v = Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)))
        lg = bpy.data.objects.new(f"LGT_{name.title()}_{preset}", bpy.data.lights.new(name, "SUN"))
        lg.data.energy, lg.data.angle = energy, math.radians(soft)
        lg.rotation_euler = (-v).to_track_quat("-Z", "Y").to_euler()
        bpy.context.scene.collection.objects.link(lg)
```

- Area lights instead of suns: size = object diameter, distance ~4× its radius, key power tuned until the lit side sits near 70 % grey in a `neutral` view transform.
- 18 % grey cove: floor and world 0.18 for `studio`, so albedo reads true.
- Lookdev loop: one change per pass, capped at 3-5 passes (`lookdev` → `review-transforms`).

Adapted from Blender Agent Skills by EL4CTEO (lookdev lighting; MIT) and the Blender MCP / AgentPMT three-point notes. Same presets as Forge `light(preset, env)`.
