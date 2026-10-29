---
description: "Bumpers (wrap-around loft, intake, splitter, fog lights, reflectors), spoilers (NACA airfoil wing, ducktail), diffuser, exhaust tips and license plates in bpy with real sizes"
metadata:
  label: "Part: bumpers, aero, exhaust, plate, wiper"
---

# Bumpers, aero, exhaust, plates, wipers

## Bumpers (origin = back centre, bottom; front grows to -Y)

Loft a closed 6-point section (y, z) across the width in 24 steps:
`[(3, h), (-0.7d, h), (-d, 0.7h), (-d, 0.28h), (-0.85d, 0), (3, 0)]`, swept back at the corners by `0.9 d × (|x| / (w/2))^4` and tapered 15 % at the ends. Caps on.

| Style | depth d × height h (cm) | Extras |
|---|---|---|
| sport | 10 × 30 | splitter 0.9 w × 8 × 1.2, side intakes |
| sedan | 12 × 34 | lower intake 0.45 w, fog lights r 3.2 |
| suv / truck | 14-16 × 40-42 | metal skid plate, step pad at the rear |
| classic | 10 × 18 | chrome bar profile |

Width on a car ≈ 0.82 × body width (the corners wrap). Rear bumper: the same loft flipped to +Y, red reflectors 0.08 w × 2 cm at the corners.

## Spoiler (origin = base centre)

Wing: NACA 4-digit thickness `yt = 5 t c (0.2969√s − 0.126 s − 0.3516 s² + 0.2843 s³ − 0.1036 s⁴)`, t = 0.12, chord 24 cm, camber −4 % (downforce), cosine spacing, lofted across 130 cm at −8° attack, 18 cm up; end plates 1 × 1.15 c × 14; uprights 2 × 8 at ±0.3 w. Sedan/classic: a ducktail wedge 14 × 4 cm. SUV: roof spoiler 26 × 5 cm. Scifi: two tiers 9 cm apart.

## Diffuser

Plate w × 40 × 1.5 cm tilted 10° up to the rear, 5 vertical strakes 1 × 36 × 7. Origin at the front edge.

## Exhaust

Pipe r 2.6 cm swept from the mount 40 cm back; tip lathe r 4.5 (truck 6) × 12 cm with a rolled lip and a dark baffle 5 cm in; sport/scifi doubles at ±5.5 cm; scifi uses a rectangular ring with an emissive core. Keep the tip inside the overall length.

## License plate

EU 52 × 11 cm, US 30.5 × 15.2 cm; plate 3 mm, raised 1.2 cm border, 2 bolts, embossed text (font curve, 3 mm extrude, height 0.45 h). The rear plate is the front plate **turned 180° about Z** so the text still reads.

## Wiper (origin = pivot)

Pivot cap r 1.6; arm 0.85 L × 1.4 × 1; rubber blade L × 0.8 × 1.4 (L = 55 cm sedan). Two pivots at the windshield base, ~0.27 W apart.

**Done when:** bumpers close the body ends with no gap from the side view, the wing sits on its uprights, and plate text reads front and back.

Forge: `car_part(kind=bumper_front|bumper_rear|spoiler|diffuser|exhaust|license_plate|wiper, style=sport)`.

---
Wing section from the NACA 4-digit formula; plate sizes from EU/US standards. Loft method adapted from Blender Agent Skills (hardsurface-modeling) by EL4CTEO, MIT licence.
