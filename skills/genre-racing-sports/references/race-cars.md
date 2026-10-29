---
description: "Race and arcade cars for racing games: class proportions (GT, rally, kart, muscle, stock, limo-for-hire), stance, aero kit, team livery zones, readable silhouettes at speed, part swaps for customisation"
metadata:
  label: "Race cars"
---

# Race cars

Build every car from the `vehicle-artist` recipes (`../../vehicle-artist/references/car-body-from-curves.md` and `../../vehicle-artist/references/parts/`); this file sets the racing look.

## Classes (cm)

| Class | L × W × H | Wheelbase | Tyre | Stance |
|---|---|---|---|---|
| GT / supercar | 445 × 195 × 120 | 265 | 255/35R19 front, 305/30R20 rear | 11 clearance, wheels flush with the arches |
| Rally hatch | 410 × 180 × 145 | 260 | 205/65R15 gravel | 20 clearance, mud flaps, roof scoop |
| Muscle | 480 × 190 × 135 | 285 | 245/45R18 | rake: rear 3 cm higher |
| Stock car | 510 × 195 × 130 | 280 | 275/40R17 slick | one door, roof flaps |
| Kart | 180 × 130 × 60 | 105 | 110/50R5 front, 130/50R5 rear | 3 clearance, open frame |
| Party / limo | 720 × 190 × 148 | 520 | 225/55R17 | long greenhouse, bench, roof lights |

## Readable at speed

- Silhouette first: wing, roof line and wheel size must read from 50 m. Tyres ≥ 1/3 of the body height on arcade cars.
- One big shape per side: a 3-colour livery (base, accent 20 %, number panel); keep stripes ≥ 15 cm wide.
- Lights: emissive ≥ 10 for night tracks; a red rear bar the full width of the tail helps chase cams.
- Avoid detail under 2 cm on LOD1+; plates, wipers and interior go at LOD1.

## Aero kit (parts you can swap)

| Part | Sport/GT | Rally | Arcade |
|---|---|---|---|
| Front | splitter 0.9 W × 8 cm, canards | skid plate | oversized intake |
| Rear | NACA wing, chord 24-30, 18-25 cm up | roof spoiler | double wing (scifi) |
| Under | diffuser, 5 strakes | none | glow strip |
| Wheels | 10-spoke or mesh, 19-20 in | 5-spoke 15 in, white | dish or 3-spoke |

Customisation garages swap one part at a time: keep each part an own mesh with its origin at its socket (hub, mount, hinge) and the same material slots, so a swap never moves or recolours the car.

## Team livery zones

UV the body so hood, doors and roof each own a clean rectangle for decals; number panels on both doors and the roof (≥ 40 cm digits). Paint is one shared material instance per team colour (`car-paint-materials.md`).

**Done when:** a chase-cam screenshot at 50 m still reads class, team colour and wing; swapping the wing or rims leaves the car in place.

Forge: `car(body=sports, parts={rim:"mesh", spoiler:"sport", diffuser:true}, paint="#0a3cff")`, then `car_swap(car, slot="spoiler", style="scifi")`.

---
Class sizes from typical production and series cars. Readability guidance adapted from Blender Agent Skills (optimization, asset-qa) by EL4CTEO, MIT licence.
