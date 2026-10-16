---
description: "Cinematic versus game hair: curves and particle grooms for renders, hair cards with atlases and LODs for real-time games"
metadata:
  label: "Cinematic vs Game Hair"
---

# Cinematic vs Game Hair

| | Game cards | Cinematic curves/particles |
|--|------------|----------------------------|
| Density | Card shells | Strand/curve count |
| Motion | Bones / soft bones / vertex wind | Sim or deform |
| Shader | Alpha clip/hash + anisotropic approx | Principled Hair |
| LOD | Drop shells | Reduce children |
