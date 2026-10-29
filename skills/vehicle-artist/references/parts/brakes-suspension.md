---
description: "Brake disc, caliper and suspension (coilover, A-arms, knuckle) recipes in bpy with real sizes; what spins with the wheel and what does not"
metadata:
  label: "Part: brakes and suspension"
---

# Brakes and suspension

## Brake disc (spins with the wheel)

| Rim | Disc diameter | Thickness |
|---|---|---|
| 15-16 in | 280 mm | 22-25 mm |
| 17 in | 320 mm | 28 mm |
| 18-19 in | 340-360 mm | 30 mm |
| 20 in+ / track | 380 mm | 32-34 mm |

Rule: disc Ø ≈ rim Ø (mm) − 110, clamped 280-380, and at most rim radius − 45 mm so the caliper clears the barrel. Inner radius 0.55 × disc radius. Build: one lathe (closed rectangle with 2 mm chamfers, 48 segments) + a hat lathe from the inner radius to the hub face. Drilled look: 12 dark 9 mm dimples on a ring at the disc mid-radius. Material metal (metallic 1, roughness 0.35-0.45).

## Caliper (fixed, does not spin)

A partial lathe: closed profile x ∈ [disc − 2 cm, disc + 2 cm] × r ∈ [disc r − 4.6, disc r + 1.2 cm], swept 5°-60° (the rear-upper arc), end caps on. Accent paint (red/yellow), roughness 0.35. In a rig it stays on the root/knuckle, not the wheel bone.

```python
lathe(prof, seg=10, a0=math.radians(5), a1=math.radians(60))   # partial sweep closes its ends
```

## Suspension (origin = hub, chassis to -X on the left side)

| Piece | Size |
|---|---|
| Knuckle | 6 × 8 × 22 cm block at x -6 |
| Lower A-arm | 2 tubes r 1.6 cm from (-8, 0, -9) to (-45, ±15, -8) |
| Upper A-arm | 2 tubes r 1.3 cm from (-8, 0, 10) to (-38, ±12, 13) |
| Damper | cylinder r 2.2 cm from (-28, 0, -7) to (-32, 0, 38) |
| Spring | helix, 6 turns, coil r 5 cm, wire r 0.8 cm around the damper axis |

Tubes: sweep a circle along the points with parallel-transport frames (or a curve with `bevel_depth`, then convert to mesh and weld). Sockets: `Hub` at the origin, `Chassis` at (-45, 0, -8).

**Done when:** the disc sits behind the spokes with ≥ 1 cm clearance, the caliper clears the barrel, and the coilover top reaches the chassis mount.

Forge: `car_part(kind=brake_disc|caliper|suspension, tire="225/45R17", disc=320)`.

---
Disc sizes from common OEM and track fitments. Sweep and lathe helpers adapted from Blender Agent Skills (hardsurface-modeling) by EL4CTEO, MIT licence.
