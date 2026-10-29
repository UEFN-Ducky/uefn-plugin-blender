---
description: "Car interior and engine recipes in bpy: bucket and bench seats, steering wheel, dashboard with gauges and screen, V8 and inline-4 engine blocks; ergonomic sizes"
metadata:
  label: "Part: seat, steering wheel, dashboard, engine"
---

# Interior and engine

Driver on the left (+X) for LHD; the occupant faces -Y.

## Seat (origin = floor centre under the cushion)

| Piece | Size (cm) |
|---|---|
| Base frame | 0.8 w × 40 × 14, plastic |
| Cushion | w 50 × 50 × 12 at z 20, bevel 4, leather |
| Backrest | w × 12 × 58 (sport 75), pivot at (0, 24, 20), tilted 15° back |
| Headrest | 26 × 10 × 18 on two chrome posts r 0.6 (sport: built into the back) |
| Bolsters (sport) | 8 × 46 × 8 on the cushion, 8 × 14 × 0.55 tall on the back |

Hip point ≈ 30 cm above the floor (sport 20). Bench (classic, limo rear): width = cabin − 50, three headrests.

## Steering wheel (origin = hub, socket Column)

Rim Ø 37 cm (sport 35, flat bottom at 80 %), grip tube r 1.6, leather; hub r 6 × 5 deep; spokes at 9, 3 and 6 o'clock; column r 2.5 × 15 into the dash. The whole wheel is tilted 20° (top leans forward) about X.

## Dashboard (origin = firewall centre, bottom)

Loft the section `[(0,0), (0,30), (8,38), (30,37), (42,26), (40,10), (28,0)]` (y, z) across the cabin width (car width − 40), 17 steps. Binnacle 36 × 12 × 10 in front of the driver with two emissive gauges r 5; a 22 × 13 emissive centre screen tilted 15°; 4 chrome vents 10 × 4.

## Engine (origin = bottom centre, crank along Y)

| Piece | V8 (sport, suv, truck, classic) | Inline-4 (sedan) |
|---|---|---|
| Block | 40 × 55 × 30 | same |
| Heads | 2 × (14 × 52 × 10) banked ±40° | 1 × 24 × 50 × 10 |
| Valve covers | accent paint | accent paint |
| Intake | plenum 16 × 40 × 10 + box filter (classic: round chrome Ø 28) | 4 runner tubes to a side plenum |
| Front | pulleys r 7 / 5 / 4 on Y | same |

**Done when:** the driver's eye point (hip + 65 cm) sees over the binnacle, the wheel clears the seat cushion by ≥ 20 cm, and the engine fits under the hood line.

Forge: `car_part(kind=seat|steering_wheel|dashboard|engine, style=sport)`; on a car `interior=true` places dash, wheel and seats.

---
Ergonomic sizes from typical passenger-car packaging. Interior budget advice adapted from Blender Agent Skills (optimization) by EL4CTEO, MIT licence.
