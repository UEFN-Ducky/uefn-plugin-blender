---
description: "Real weapon proportions in cm: overall, barrel, height, grip angle, hand fit for rifles, pistols, shotguns, SMGs, snipers, knives, swords, axes, hammers"
metadata:
  label: "Weapon proportions"
---

# Weapon proportions

Block out at real size first (1 Blender unit = 1 m, model in cm values / 100). A gun that is 10 % off reads as a toy.

## Guns

| kind | reference | overall | barrel | height | width | grip angle |
|---|---|---|---|---|---|---|
| rifle | M4 / AR-15 | 75.6-84 (stock in/out); AR-15 rifle 100 | 36.8 (14.5"); 40.6 (16"); 50.8 (20") | 24 with 30-rd mag | 6.5 | 25° |
| rifle | AK-47 / AKM | 88 | 41.5 | 24 | 7 | 20° |
| pistol | Glock 17 | 20.2 | 11.4 | 13.9 | 3.2 | 22° |
| pistol | M1911 | 21.6 | 12.7 | 13.3 | 3.3 | 18° |
| pistol | Desert Eagle | 27 | 15.2 | 15 | 3.2 | 18° |
| smg | MP5 | 55 folded / 70 | 22.5 | 26 with mag | 5 | 15° |
| shotgun | Remington 870 | 100-106 | 46-71 | 21 | 6 | 35° (straight stock) |
| sniper | bolt action (M24 / AWM) | 109-125 | 61-69 | 25 with scope | 7 | 10-15° |

Fixed parts (cm): Picatinny rail 2.12 wide, slots every 1.0; M-LOK slots 3.2 x 0.7 every 4.0; sight height over bore AR 6.4; length of pull (stock to trigger) 33-36; 30-rd 5.56 mag ~18 tall with 9° curve; pistol mag base 3.4 x 2.4; trigger guard opening 2.5 tall x 4-5 long (gloved finger). Bore: 5.56 mm rifle, 9 mm pistol, 7.62 mm battle rifle, 18.5 mm 12 ga.

## Hand fit

| measure | cm |
|---|---|
| grip circumference | 13-15 (pistol), 14-16 (rifle grip) |
| grip depth front-back | 4.5-5.5 |
| trigger reach (backstrap to trigger face) | 6.8-7.5 |
| palm width (hand on grip) | 8-9 |
| handle length, one-hand melee | 10-12 (one fist); two-hand 25-30 |

## Melee

| kind | overall | blade | handle | blade thickness (base → tip) | width |
|---|---|---|---|---|---|
| combat knife (Ka-Bar) | 30 | 17.8 | 11 | 0.6 → 0.2 | 3.2 |
| dagger | 30-40 | 20-28 | 10-12 | 0.6 → 0.15 | 3-4 |
| katana | 100 | 60-73 (sori 1.5 curve) | 25-30 | 0.7 → 0.5 | 3.2 → 2.5 |
| arming sword | 90-95 | 70-80 | 10-12 + pommel | 0.6 → 0.2 | 5 → 2 |
| longsword | 110-125 | 85-95 | 20-28 | 0.6 → 0.2 | 5 → 2 |
| hatchet | 35-45 | bit 10 tall | 30-40 haft | eye 3 → edge 0.1 | haft 2.4 x 3.2 |
| felling / battle axe | 70-90 | bit 15-20 tall, beard drop 10-16 | 65-80 | eye 4 → edge 0.1 | |
| war hammer | 60-80 | head 6.5 x 6.5 x 12 | 55-70 | | |
| sledge | 90 | head 6.5 x 6.5 x 17 | 85 | | |

Katana parts: tsuba (guard) Ø 7.5, habaki 2.4 long, kashira (pommel cap) 1.2. Balance point: swords 10-15 cm in front of the guard; axes and hammers far forward (in the head).

## Stylized

Keep the real ratios and push one: chunkier cross-sections x1.2-1.3, a bigger mag or blade x1.1-1.2, bevels 2-3x the realistic width. Never shrink the grip below the hand table above: the hand mesh will clip.

## Quick check

```python
import bpy
d = bpy.context.active_object.dimensions * 100  # cm
print("L %.1f  W %.1f  H %.1f cm" % (d.x, d.y, d.z))  # compare with the tables
```

---
Measurements are from public manufacturer specifications (Glock, Colt, H&K, Remington, Magpul M-LOK, MIL-STD-1913 Picatinny) and common sword-making references.
