---
description: "Realistic head blockout from Loomis/Reilly proportions: landmark heights, widths, ear and eye spacing in head units, a bpy landmark rig and the checks"
metadata:
  label: "Head blockout (proportions)"
---

# Head blockout from proportions

Block the skull and landmarks before any feature. H = chin to crown. An adult is H ≈ 0.23–0.24 m; a Fortnite-scale hero head is ≈ 0.25 m.

## Landmarks (fraction of H, chin = 0)

| Landmark | Height | Width / depth |
|---|---|---|
| Crown | 1.0 | skull width 0.62 H; depth 0.80 H |
| Hairline | 0.86 | — |
| Brow ridge | 0.585 | brow span 0.46 H |
| **Eye line** | **0.50** | pupils ±0.13 H; fissure 0.125 H wide; gap between eyes = one eye width |
| Nose base | 0.30 | alar width = inner-eye gap (0.13 H) |
| Mouth line | 0.205 (⅓ nose base → chin) | corners under the irises (±0.10 H) |
| Chin | 0.0–0.07 | chin pad 0.10 H wide |
| Ears | 0.30 → 0.585 (nose base to brow) | just behind the head centre, tilted back ~15° |
| Jaw angle | 0.15 | bigonial width 0.48 H |

Thirds: hairline→brow = brow→nose base = nose base→chin (each ≈ 0.29 H). In profile, the face plane leans about 10° back from the brow to the chin.

**Sex / age / build** (relative to neutral):

- Male: brow ridge ×1.4, jaw ×1.06, chin ×1.3, lips ×0.85.
- Female: brow ×0.55, jaw ×0.93, lips ×1.2.
- Child: eye line drops to 0.44 H, nose ×0.65, eyes ×1.12, H 0.19 m.
- Elder: nasolabial depth ×2.6, lips ×0.7, nose and ears ×1.12–1.15.

## One-call base (fastest)

Forge builds this whole blockout plus loops, eyes, teeth and skin: `forge_hq op=head params={"sex":"female","age":"adult"}`. See `forge/realistic_head`. Use the recipe below only to block a head by hand in Blender.

## bpy landmark rig

Run with `blender_execute_blender_code`. It drops empties at every landmark so sculpting and shrinkwrapping have targets.

```python
import bpy
H = 0.24
L = {"crown": (0, 0, 1), "brow": (0, -0.36, .585), "eye_L": (.13, -.33, .5), "eye_R": (-.13, -.33, .5),
     "nose_base": (0, -.40, .30), "mouth": (0, -.37, .205), "chin": (0, -.30, .03),
     "ear_L": (.31, .03, .44), "ear_R": (-.31, .03, .44), "jaw_L": (.24, -.05, .15), "jaw_R": (-.24, -.05, .15)}
for name, (x, y, z) in L.items():
    e = bpy.data.objects.new("LM_" + name, None)
    e.empty_display_size = 0.01
    e.location = (x * H, y * H, z * H)
    bpy.context.scene.collection.objects.link(e)
```

Block the cranium as a UV sphere scaled to (0.62, 0.80, 1.0)·H/2. Then pull the jaw and chin forward, flatten the face plane, and push in the eye sockets about 0.035 H.

## Done when

- `blender_get_viewport_screenshot` front and side: the eye line crosses the middle of the head bounds (±3%), and the ear top lines up with the brow and the ear bottom with the nose base.
- `blender_get_object_info`: dimensions z = H, x ≈ 0.62 H.

## Don't

- Don't put the eyes in the upper third. That is the most common amateur error: the eyes sit at half height.
- Don't place features before the skull mass reads right in profile.

---
Proportions: Loomis / Reilly canon in our own words. MIT, uefn-ducky.
