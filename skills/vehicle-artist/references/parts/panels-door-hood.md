---
description: "Door with inner panel and hinge pivot, hood, trunk, fender with wheel arch, window glass and mirror in bpy: panel thickness, 3-5 mm gaps, hinge origins"
metadata:
  label: "Part: door, hood, trunk, fender, window, mirror"
---

# Door, hood, trunk, fender, window, mirror

Panels are sheets with thickness (sheet metal reads as 8-12 mm in games), with chamfered or rolled edges and a 3-5 mm gap to the next panel.

## Panel helper: a closed slab

Sample a surface P(u, v) on a grid, offset a copy along -normal by the thickness and join the borders: every edge has two faces.

```python
def slab(bm, P, nu, nv, t):
    top = [[bm.verts.new(P(i/nu, j/nv)) for j in range(nv+1)] for i in range(nu+1)]
    def n(i, j):
        du = top[min(i+1, nu)][j].co - top[max(i-1, 0)][j].co
        dv = top[i][min(j+1, nv)].co - top[i][max(j-1, 0)].co
        return du.cross(dv).normalized()
    bot = [[bm.verts.new(top[i][j].co - n(i, j)*t) for j in range(nv+1)] for i in range(nu+1)]
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((top[i][j], top[i+1][j], top[i+1][j+1], top[i][j+1]))
            bm.faces.new((bot[i][j], bot[i][j+1], bot[i+1][j+1], bot[i+1][j]))
    ring = [(i, 0) for i in range(nu)] + [(nu, j) for j in range(nv)] + \
           [(i, nv) for i in range(nu, 0, -1)] + [(0, j) for j in range(nv, 0, -1)]
    for k, (i, j) in enumerate(ring):
        i2, j2 = ring[(k+1) % len(ring)]
        bm.faces.new((top[i][j], bot[i][j], bot[i2][j2], top[i2][j2]))
```

Or Solidify (thickness 0.01, offset −1, `use_rim=True`) + Bevel (width 2.5 mm, segments 2, limit Angle 30°) on a sheet, then apply.

## Door (left side on +X, hinge on the front edge)

| Part | Size (cm) |
|---|---|
| Outer skin | length 105 (sedan front) / 120 (coupe), height 70 to the belt, 1 cm thick, bulge 2.5 cm at mid-height |
| Inner trim | 2 cm panel at x -5.5, inset 3-4 cm all round, plastic |
| Armrest | 5 × 0.4 L × 3 at 62 % height, leather |
| Shut faces | 5.5 cm strips front, back and bottom joining skin to trim |
| Handles | outer chrome 14 × 2.5 at 72 % length, 82 % height; inner chrome 8 cm |
| Glass | 40 cm tall, 5 mm, leaning in 4 cm (tumblehome), front edge raked 45 % for front doors |

**Origin on the hinge line** (front edge, bottom) so the door swings about local Z. Rear doors: rake 15 %. Sedan/SUV: a painted frame tube r 1.2 cm around the glass; coupes are frameless.

## Hood and trunk

Hood 150 × 135 cm, crown 4 cm across, front edge 14 cm lower; **origin at the rear hinge (windshield end)**. Trunk 150 × 85 cm, origin at the front hinge edge. Sport: two plastic vents on the hood, a lip on the trunk; SUV/truck: a 3 cm power bulge.

## Fender with the wheel arch

Arch radius = tyre radius + 4.5 cm. Make a grid over y ∈ [−arch − 25, arch + 20], z ∈ [−R + 10, R + 30] around the hub; drop faces whose centre is inside the arch circle; snap the new boundary verts onto the circle; flare x outward by 2.5 cm × e^(−(d − arch) / 6); then solidify + bevel. Origin at the hub.

## Window and mirror

Window: a curved glass slab (bend 3 cm, top 25 % narrower), 5 mm, origin at the bottom centre.
Mirror (left on +X, origin at the door mount): arm 8 × 3 × 2.5 plastic; housing 22 × 10 × 12 painted with a 3.5 cm bevel; mirror glass 0.6 cm, chrome; an emissive turn-signal strip on the front face. Truck: 20 × 10 × 30 tow mirror.

Right-side copies: mirror on X and recalculate normals, then **apply scale** so UEFN gets scale 1 (or duplicate and rotate 180° about Z for parts with no handedness).

**Done when:** the door swings about its hinge without leaving the body outline (rotate local Z 60°, screenshot, undo), panel gaps read at 3/4 view, and each panel's edges are all two-faced.

Forge: `car_part(kind=door|hood|trunk|fender|window|mirror, side=left|right)`.

---
Panel thickness and gap numbers from production body tolerances (3-5 mm). Solidify/bevel stack adapted from Blender Agent Skills (hardsurface-modeling) by EL4CTEO, MIT licence.
