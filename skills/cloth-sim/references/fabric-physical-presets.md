---
description: "Physical cloth presets with exact Blender values for cotton, denim, leather, silk and rubber: vertex mass, tension, compression, shear, bending, air damping, quality steps"
metadata:
  label: "Fabric Physical Presets"
---

# Fabric Physical Presets

Scale applied, real size (a cape is ~1.2 m). Pre-roll 20-60 frames before the shot.

| Fabric | Mass (kg) | Air | Tension / Compression | Shear | Bending | Quality | Notes |
|---|---|---|---|---|---|---|---|
| cotton | 0.3 | 1 | 15 / 15 | 15 | 0.5 | 5 | default shirt / cape |
| denim | 1.0 | 1 | 40 / 40 | 40 | 10 | 12 | stiff folds |
| leather | 0.4 | 1 | 80 / 80 | 80 | 150 | 15 | holds shape, few folds |
| silk | 0.15 | 1 | 5 / 5 | 5 | 0.05 | 5 | flows, needs collision distance 3 mm |
| rubber | 3.0 | 1 | 15 / 15 | 15 | 25 | 7 | bouncy, heavy |

```python
FABRIC = {"cotton": (0.3, 15, 15, 0.5, 5), "denim": (1.0, 40, 40, 10, 12), "leather": (0.4, 80, 80, 150, 15),
          "silk": (0.15, 5, 5, 0.05, 5), "rubber": (3.0, 15, 15, 25, 7)}
def fabric(obj, kind):
    mass, tens, shear, bend, q = FABRIC[kind]
    s = (obj.modifiers.get("Cloth") or obj.modifiers.new("Cloth", "CLOTH")).settings
    s.mass, s.air_damping, s.quality = mass, 1.0, q
    s.tension_stiffness = s.compression_stiffness = tens
    s.shear_stiffness, s.bending_stiffness = shear, bend
```

Pins, collisions and baking to bones or shape keys: `pin-and-collide.md`, `bake-targets.md`.

Values follow Blender's built-in cloth presets. Adapted from Blender Agent Skills by EL4CTEO (simulation; MIT).
