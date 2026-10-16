---
description: "Cloth pins and collision: pin collars, waistbands and seams with soft falloff, simplified body colliders, and the bake path"
metadata:
  label: "Pins & Collision"
---

# Pins & Collision

## Pins
- Collar, waistband, shoulder seams, belt loops
- Paint soft falloff — hard binary pins crease badly

## Colliders
- Simplified body (capsules or low mesh)
- Thickness margin scaled to character size
- Disable self-collision first; enable if needed carefully

## Bake Path
Settle → animated collide → corrective sculpt/shape keys → export
