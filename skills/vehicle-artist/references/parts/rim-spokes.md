---
description: "Rim recipe in bpy: barrel and lip lathe, concave face, 5 / 10 split / mesh / dish / n spoke patterns, lug nuts, centre cap; real rim widths per tyre"
metadata:
  label: "Part: rim and spokes"
---

# Rim and spokes

## Sizes

| Tyre | Rim width | Bead seat radius | Hub radius |
|---|---|---|---|
| 205/55R16 | 6.5 in (16.5 cm) | 20.3 cm | 6.1 cm |
| 225/45R17 | 7.5 in (19 cm) | 21.6 cm | 6.5 cm |
| 255/35R19 | 8.5-9 in (22 cm) | 24.1 cm | 7.2 cm |

Rim width ≈ 0.85 × tyre section width. Lip 1.4 cm above the bead seat, barrel wall 1 cm, face set back 2.5-4 cm (sport = deeper dish). 5 lug nuts on a 114.3 mm circle (r ≈ 0.62 × hub radius × 1.75), hex nuts = 6-sided cylinders r 0.9 cm.

## Barrel (one lathe)

Closed profile in (x along the axle, r), face on +X; revolve 48 segments:

```python
o, lip, rr = 0.095, 0.014, 0.216        # half width, lip, bead seat (m)
barrel = [(o, rr+lip), (o-.010, rr+lip), (o-.012, rr-.001), (-o+.012, rr-.001),
          (-o+.010, rr+lip), (-o, rr+lip), (-o, rr-.011), (o, rr-.011)]
```

Use the same `lathe(prof, seg)` helper as the tire (rings of verts, quads between profile points, faces cyclic).

## Spoke patterns

Each spoke is a closed six-sided block from 8 corners: at the hub (r0 = 0.85 × hub r, face x = xf + 0.8 cm) and at the barrel (r1 = rr - 0.9 cm, x = o - 1.4 cm), width w0 → w1, thickness 2.4-2.6 cm. Corner `= x̂·x + d·r + t·(±w/2)` with `d = (0, cos φ, sin φ)` and `t = (0, -sin φ, cos φ)`.

| Pattern | Spokes | w0 / w1 |
|---|---|---|
| `5` | 5 at 72° | 0.95 hub r / 0.34 rr |
| `10` (5 split) | pairs at φ ± 7° | 0.42 hub r / 0.12 rr |
| `mesh` | 10 + 10, twisted ±22°, the second set 1 cm deeper | 1.6 / 1.9 cm |
| `dish` (steel) | a lathe disc from the hub to the barrel + 8 dark vent pockets + chrome cap | — |
| `n` (2-20) | n at 360/n | min(hub, 1.7 rr / n) |

Radial alternative: model one spoke at 12 o'clock with its origin at the hub, then Array with an object offset empty rotated 360/n about X (see `bpy-vehicles.md`), apply, join.

## Finish

Smooth by angle 30°, bevel 2 mm on spoke edges (segments 2) or weighted normals for mid-poly. Material: chrome or painted alloy (metallic 1, roughness 0.2), dark plastic for the vent pockets and centre bore.

**Done when:** the rim seats inside the tire bead (barrel top = bead seat radius), the spokes touch hub and barrel with no gap, and a front screenshot shows the pattern.

Forge: `car_part(kind=rim, spokes="10")`, or on a car `car_swap(car, slot="rim", spokes="mesh")`.

---
Rim widths and bolt circles from common OEM fitments. Radial-array method adapted from Blender Agent Skills (hardsurface-modeling) by EL4CTEO, MIT licence.
