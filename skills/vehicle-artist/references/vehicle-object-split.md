---
description: "Vehicle object split: body, wheels, doors and turrets as separate objects, and collision from convex body pieces and wheel capsules"
metadata:
  label: "Vehicle Object Split"
---

# Vehicle Object Split

| Object | Animate? | LOD keep until |
|--------|----------|----------------|
| Body | Rare | LOD3 |
| Wheels | Yes | LOD2 |
| Calipers | Optional | LOD1 |
| Glass | No | LOD2 |
| Lights | Emissive | LOD2 |
| Interior | No | LOD1 (drop after) |
| Wipers/mirrors | Optional | LOD0–1 |

Collision: body convex pieces + wheel cylinders/capsules.
