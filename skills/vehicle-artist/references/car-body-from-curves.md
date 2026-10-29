---
description: "Car body in bpy: real proportions per body style, blueprint planes at scale, a body loft from side/top/front profile curves to sub-d, splitting panels along real seams with 4 mm gaps, wheel arches and glass"
metadata:
  label: "Car body from curves"
---

# Car body from profile curves

## 1. Proportions (cm, lock these first)

| Body | L × W × H | Wheelbase | Clearance | Tyre | Front overhang share |
|---|---|---|---|---|---|
| sedan | 480 × 185 × 145 | 280 | 14 | 225/45R17 | 0.44 |
| coupe | 460 × 185 × 135 | 270 | 13 | 245/40R18 | 0.44 |
| hatch | 410 × 178 × 148 | 260 | 14 | 205/55R16 | 0.46 |
| suv | 480 × 195 × 175 | 285 | 21 | 255/55R19 | 0.45 |
| pickup | 560 × 200 × 190 | 340 | 23 | 265/70R17 | 0.40 |
| limo | 720 × 190 × 148 (600-900) | L − 200 | 14 | 225/55R17 | 0.42 |
| sports | 445 × 195 × 120 | 265 | 11 | 255/35R19 | 0.45 |
| van | 520 × 200 × 200 | 330 | 17 | 235/65R16 | 0.30 |
| classic | 470 × 180 × 140 | 275 | 16 | 205/70R15 | 0.45 |
| kart | 180 × 130 × ~60 | 105 | 3 | 110/50R5 | 0.45 |

Front axle y = −L/2 + (L − wheelbase) × share; track = W − tyre width − 8; hub z = tyre radius (wheels on z = 0). A limo stretches only between the axles.

## 2. Blueprint planes at real scale

Side, front and top images as image empties sized to the car (`empty_display_size` = L in metres for the side and top, W for the front), alpha 0.4, ortho-only (`show_empty_image_perspective = False`), pushed past the body. Recipe: `bpy-vehicles.md` § Blueprint reference setup. Check each silhouette in ortho before any detail.

## 3. Profile curves → sections

Describe the car as three curves sampled along f ∈ [0, 1] (front → back):

- **top (plan)**: half width `w(f) = W/2 (0.8 + 0.2 (1 − |2f − 1|⁴)^¼)`, rounded corners;
- **side**: roof line `z_top(f)`: hood from 0.58 H at the nose to the belt at the windshield base `a0`, windshield to H at `a1`, roof to `c1`, rear glass down to the deck at `c2`, deck to the tail. Greenhouse (a0, a1, c1, c2): sedan .33/.46/.70/.82, hatch .33/.46/.86/.96, suv .32/.43/.90/.97, sports .38/.52/.64/.90, limo .22/.30/.82/.90;
- **front (section)**: 9 control points from the bottom centre round to the roof centre: floor, rocker, door bulge (max width), shoulder at the belt (0.62 H), greenhouse base, roof edge, roof centre. Tumblehome g = clamp((z_top − belt) / (H − belt)) pulls the glass 8-28 cm inboard.

Sample each section with Catmull-Rom (mirror the end points across x = 0 for a smooth centreline), mirror for the right side, and loft rows of sections into one quad grid (about every 8 cm along the length, 26 points per half section). Cap both ends (they hide behind the bumpers).

Sub-d route: keep this as a light cage (12-16 sections × 12 points), add Subdivision level 2 with creases 0.85 on seam loops, and apply at level 1 for the game mesh.

## 4. Panels along real seams, 4 mm gaps

Put grid lines exactly on the seams (insert their f and t values into the samples) so every panel is a clean block of faces. Seams: belt (t 0.58), rocker (0.20), floor (0.10), side glass (0.63-0.83), windshield/rear glass (above 0.66), door cuts between the arches, hood at a0, trunk at c2.

```python
lay = bm.faces.layers.int.new("panel")          # label every face, then per panel:
pb = bm.copy(); pl = pb.faces.layers.int["panel"]
bmesh.ops.delete(pb, geom=[f for f in pb.faces if f[pl] != idx], context="FACES")
for v in {v for e in pb.edges if len(e.link_faces) == 1 for v in e.verts}:   # inset 2 mm
    c = sum((f.calc_center_median() for f in v.link_faces), Vector()) / len(v.link_faces)
    d = c - v.co; d -= v.normal * d.dot(v.normal); v.co += d.normalized() * 0.002
```

Then Solidify 10 mm (glass 5 mm, offset −1, rim on) + Bevel 2.5 mm, 2 segments, angle 30°. Real gaps are 3-5 mm; under 3 mm they vanish at game distance.

## 5. Wheel arches

Delete body faces whose centre is within arch r = tyre r + 4.5 cm of the hub (side view) and outboard of W/2 − 32 cm; snap the new boundary verts onto the circle; add a black plastic liner (a half-tube from W/2 − 32 to W/2 − 4 plus an inner wall disc, swept from just below the hub height over the top).

## 6. Origins

Doors on the hinge line (front edge), hood on the rear hinge, trunk on the front hinge; everything else at the car origin (ground centre). Glass in doors moves with the door.

**Done when:** side/front/top ortho screenshots sit on the blueprints, overall size is within 5 %, every panel is closed, the gaps read at 3/4 view and all four tyres touch z = 0 inside their arches.

Forge: `car(body=sedan|...|limo, length_cm=720)` does all of this in one op.

---
Section-loft and seam method original to Ducky; build-order ideas adapted from Blender Agent Skills (hardsurface-modeling) by EL4CTEO, MIT licence. Dimensions from typical OEM specs.
