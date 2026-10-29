---
description: "Realistic eyes (sclera, recessed iris, cornea dome, tear line, caruncle) and the mouth interior (teeth arch, gums, tongue, mouth bag) with sizes and bpy"
metadata:
  label: "Eyes, teeth and mouth bag"
---

# Eyes, teeth and mouth bag

## Eye layers (sizes for a 0.24 m head)

| Part | Size | Material |
|---|---|---|
| Eyeball (sclera) | Ø 24 mm, pivot at its centre | off-white (0.82, 0.78, 0.74), rough 0.25, faint vein noise, SSS 0.5 |
| Cornea dome | radius of curvature 7.8 mm, bulges ~5 mm beyond the limbus plane | transmission/alpha ≈ 0.06, rough 0.0, IOR 1.376, clear coat 1 (wet) |
| Iris | Ø 12 mm, **2 mm behind the cornea apex**, slightly concave | radial fibre noise; brown (0.16, 0.07, 0.025) … blue (0.10, 0.22, 0.42) |
| Pupil | Ø 3–5 mm | near-black 0.004 |
| Caruncle | 4 × 6 mm pink bump in the inner corner | (0.7, 0.3, 0.3), rough 0.15, SSS |
| Tear line | 1–2 mm strip along the lower lid margin | alpha 0.3, rough 0 |
| Lid margin | lid sits 0.3–1 mm off the eyeball surface | skin |

The recessed iris under a clear dome gives true parallax, so the eye tracks the camera. A single painted sphere always reads dead.

```python
import bpy, bmesh
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=16, radius=0.012)
me = bpy.data.meshes.new("Eye_L"); bm.to_mesh(me); bm.free()
eye = bpy.data.objects.new("Eye_L", me); bpy.context.scene.collection.objects.link(eye)
eye.location = (0.031, -0.066, 0.12)        # pupil x = 0.13 H, eye line 0.5 H
eye.rotation_euler = (1.5708, 0, 0)         # poles on the gaze axis (-Y)
```

Aim the eyes with a Damped Track constraint per eye on one shared target 1–2 m ahead. Never rotate the head mesh.

## Mouth interior

| Part | Numbers |
|---|---|
| Arch | parabola y = y₀ + 30·x² (H units); 45 mm across the molars |
| Upper incisors | 8.5 mm wide, 10.5 mm tall, front face 3 mm behind the lip surface |
| Visible teeth | 2 incisors, 2 laterals, 2 canines, 4 premolars per arch (molars hidden) |
| Gums | 9–11 mm tube following the arch, (0.55, 0.17, 0.17), rough 0.3, SSS |
| Tongue | 50 × 70 × 18 mm, rough 0.45, bump noise |
| Mouth bag | 3–4 rings from the lip seam back 0.15 H, widening to 0.085 H, closed; dark red (0.22, 0.04, 0.04) |

Teeth are off-white, never pure white: (0.80, 0.76, 0.66), rough 0.25, light SSS. Split upper and lower so the jaw bone can carry the lower arch.

## Forge shortcut

`forge_hq op=head` builds all of the above: `_eye_L/_R` (sclera, cornea, iris, pupil), `_eyewet`, `_teeth_U/_L`, `_tongue`, and the mouth and socket bags.

## Done when

Front and three-quarter `blender_get_viewport_screenshot`: the iris shifts against the cornea highlight between the views, no sclera shows above the iris at rest, the teeth only show when the lips part, and no light leaks through the mouth bag.

---
Anatomical sizes are textbook averages, in our own words. MIT, uefn-ducky.
