---
description: "Vehicle LOD targets: triangle budgets per LOD and baking panel lines into normal maps for lower LODs"
metadata:
  label: "Vehicle LOD Targets"
---

# Vehicle LOD Targets

| LOD | Goal |
|-----|------|
| 0 | Full panels, visible interior if cabin readable |
| 1 | Remove bolts/seals; simplify glass frames |
| 2 | Body + wheels + glass + lights |
| 3 | Hull blob + wheel discs |

Bake panel lines to normal from LOD0 → lower when needed.
