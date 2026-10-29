---
description: "Sci-fi weapon shape language: real archetype plus one exaggeration, shape ratios, angle families, chamfer rules, glow budget, colour coding and faction styles"
metadata:
  label: "Sci-fi weapon shapes"
---

# Sci-fi weapon shape language

Start from a real archetype (rifle, pistol, SMG table in `weapons-proportions.md`) so the hand, sight line and mag still make sense, then exaggerate **one** thing: a bigger shroud, a power cell instead of a mag, a fin, an emitter.

| rule | numbers |
|---|---|
| shape ratio | big 70 % : medium 20 % : small 10 % of the silhouette; small detail clusters near hands and muzzle |
| angle family | pick 2 angles (e.g. 15° and 45°) and repeat them on every cut, wedge and vent |
| chamfers | large 45° chamfers 5-10 % of the part height on the big forms, 1.5-2 mm on the rest |
| sections | chunkier than real: x1.2-1.4 height on receiver and shroud; barrel x1.3-1.5 radius or a hex / octagon section |
| panel gaps | 1-2 mm wide, follow construction seams; no gap crosses a moving part |
| glow | 5-10 % of the surface, recessed 1-2 mm into a channel (never flush); emission 3-8 in Blender, 5-20 in UE |
| heat | vents / heat sinks within 15 cm of the chamber or emitter; orange-red heat glow |
| asymmetry | one side busier (ejection / cell port, right side); the camera side in FPS (right) gets the detail |

Colour coding: cyan / blue = energy, orange = heat or kinetic, green = bio or toxic, red = danger / enemy, white-grey panels + one accent = clean military.

| faction | shapes | materials |
|---|---|---|
| clean military | wedges, 45° chamfers, flush panels, few bolts | white / grey polymer, black metal, orange accent |
| industrial | boxes, exposed bolts every 3-5 cm, pipes, hazard stripes | painted steel with heavy edge wear, yellow / black |
| alien | no straight lines, tapering curves, ribbing | iridescent, wet roughness 0.15-0.3, bioluminescent glow |
| retro | rounded tubes, fins, rings, chrome | chrome (metallic 1, roughness 0.05), red / cream paint |

Done when: the side silhouette still shows grip, trigger guard, power cell / mag and sight as separate shapes, every cut uses the chosen angles, and glow stays under 10 % of the surface in a three-quarter render.

Forge path: `{"tool": "forge_hq", "op": "weapon", "params": {"kind": "scifi_rifle"}}` or `scifi_pistol` (hex shroud, glow strips, power cell, emitter).

---
Shape-ratio and detail-hierarchy rules adapted from Blender Agent Skills (hardsurface-modeling) by EL4CTEO, MIT licence.
