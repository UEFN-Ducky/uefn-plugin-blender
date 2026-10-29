---
description: "FACS-lite blendshape set for game heads: 16 shapes mapped to action units and ARKit names, with vertex-group masks and magnitudes"
metadata:
  label: "FACS-lite blendshapes"
---

# FACS-lite blendshapes

Sixteen shapes cover the dialogue and emotion range of most game heads. ARKit 52 is the full set: build these 16 first, then split L/R.

| Shape | FACS AU | ARKit name | Mask group | Peak move (H = 0.24 m) |
|---|---|---|---|---|
| blink_L/R | AU45 | eyeBlink | eyes | upper lid to the lower lid margin, 9–11 mm |
| squint_L/R | AU6/7 | eyeSquint | eyes + cheeks | lower lid up 2 mm, cheek up 2 mm |
| brow_up | AU1+2 | browInnerUp / browOuterUp | brows | 6–8 mm up, forehead compresses |
| brow_down | AU4 | browDown | brows | 4 mm down and 2 mm in |
| smile_L/R | AU12 | mouthSmile | lips + cheeks | corner 8 mm up and out, cheek 3 mm up |
| frown | AU15 | mouthFrown | lips | corners 4 mm down |
| jaw_open | AU26 | jawOpen | jaw | chin 15–20 mm down and 4 mm back (rotate about the ear axis) |
| pucker | AU18 | mouthPucker | lips | lips 5 mm forward, width −30% |
| funnel | AU22 | mouthFunnel | lips | lips flare 3 mm out from the seam |
| lip_press | AU24 | mouthPress | lips | seam closed, lips 1 mm flatter |
| nose_sneer | AU9 | noseSneer | nose | alae 2 mm up, nasolabial deepens |
| cheek_puff | AU34 | cheekPuff | cheeks | cheeks 6 mm out |

Visemes (AA, EE, OH, OO, FV, MBP, L, TH) mix `jaw_open`, `pucker`, `funnel` and `lip_press`. Add them as separate shapes only when you need lip-sync quality.

## bpy pattern (via `blender_execute_blender_code`)

```python
import bpy, numpy as np
ob = bpy.data.objects["Head"]
if not ob.data.shape_keys: ob.shape_key_add(name="Basis", from_mix=False)
grp = ob.vertex_groups["jaw"].index
base = np.array([v.co[:] for v in ob.data.vertices])
w = np.array([next((g.weight for g in v.groups if g.group == grp), 0.0) for v in ob.data.vertices])
pivot = np.array([0, 0.007, 0.105])                   # ear axis, metres
ang = np.radians(14) * w
co = base.copy(); d = base - pivot
co[:, 1] = pivot[1] + d[:, 1] * np.cos(ang) - d[:, 2] * np.sin(ang)
co[:, 2] = pivot[2] + d[:, 1] * np.sin(ang) + d[:, 2] * np.cos(ang)
ob.shape_key_add(name="jaw_open", from_mix=False).data.foreach_set("co", co.ravel())
```

Masks come from the vertex groups `eyes lips brows jaw nose cheeks`. Forge `head` writes these, and Forge `face_shapes(ids, set=arkit52|basic12)` builds the full set on them.

## Done when

At value 1, each shape screenshots without lip tearing (the mouth bag follows), lid intersection or pinching at poles. Combined smile + jaw_open + blink still reads.

---
FACS action units (Ekman & Friesen) referenced by number only; ARKit names are Apple's public blendshape identifiers. MIT, uefn-ducky.
