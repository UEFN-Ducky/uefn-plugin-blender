---
description: "Headlight, taillight and grille recipes in bpy: housing, chrome reflector bowls, projector, emissive DRL, lens; honeycomb, slat and bar grilles; real sizes by style"
metadata:
  label: "Part: lights and grille"
---

# Lights and grille

All face -Y (front); a taillight is built the same way and flipped to +Y. Origin = the back centre (mount).

## Sizes (w × h × depth, cm)

| Style | Headlight | Taillight | Grille |
|---|---|---|---|
| sport | 55 × 14 × 18 | 45 × 14 × 12 | 70 × 16 honeycomb |
| sedan | 60 × 22 × 20 | 45 × 14 × 12 | 80 × 24 chrome slats |
| suv | 50 × 25 × 22 | 45 × 14 × 12 | 90 × 34 bars |
| truck | 45 × 30 × 20 | 45 × 14 × 12 | 110 × 45 bars + centre post |
| classic | round Ø 20 | round Ø 14 | 60 × 36 vertical chrome |
| scifi | 75 × 6 × 14 strip | 80 × 5 strip | 100 × 8 light lines |

On a car keep each headlight ≤ 24 % of the body width.

## Headlight layers (front to back)

1. **Lens**: rounded box (w − 0.4, 1, h − 0.4) at y = −d + 0.5, bevel 1 cm; glass (roughness 0.02, alpha 0.35, IOR 1.5).
2. **DRL**: a tube r 0.5 cm along the lower edge just behind the lens; emissive white 6 (taillight: a U-shaped loop, emissive red 4).
3. **Projector**: emissive disc r 0.35 × bowl r inside each bowl.
4. **Reflector bowls**: 1 bowl (2 when w > 2.4 h), r = min(0.4 h, w / 2n × 0.8), a closed thick parabola lathe pointing -Y; chrome (metallic 1, roughness 0.05).
5. **Housing**: rounded box (w, 0.6 d, h), dark plastic.

```python
m = Matrix.Translation((x, -0.6*d, 0)) @ Matrix.Rotation(-math.pi/2, 4, 'Z')    # lathe axis X -> -Y
lathe([(0, rb*.3), (db, rb), (db, rb*.9), (.004, rb*.22)], 24, matrix=m)      # bowl, db = 0.25 d
```

Taillight: lens red (base 0.45, 0.01, 0.01, alpha 0.7) over emissive red. Classic round: chrome cup + domed lens lathe + chrome bezel ring.

## Grille

Frame: a ring prism between two rounded rectangles (outer w × h, corner 0.3 h; inner inset 2.2 cm), 4 cm deep; a dark backing plate 0.6 cm behind so the car never shows through. Fill:

- **honeycomb (sport)**: 1.9 cm cubes turned 45° about Y on a 3.2 cm grid, dark plastic;
- **slats (sedan)**: 5 horizontal chrome bars, 2.6 cm deep;
- **bars (suv/truck)**: 3 thick bars + a vertical centre post;
- **vertical (classic)**: chrome slats every 3.5 cm;
- **light lines (scifi)**: 3 emissive strips.

**Done when:** at night lighting the DRL and projectors glow through the lens, the reflector reads as chrome behind glass, and nothing shows through the grille.

Forge: `car_part(kind=headlight|taillight|grille, style=sport)`.

---
Light layering after real projector headlamps; emissive and glass values adapted from Blender Agent Skills (pbr-materials) by EL4CTEO, MIT licence.
