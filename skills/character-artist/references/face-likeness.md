---
description: "Likeness from front and side reference photos: camera setup, landmark matching, silhouette IoU targets and the fix loop"
metadata:
  label: "Face likeness from refs"
---

# Likeness from front and side refs

1. **References**: a front and a 90° side photo, shot with a long lens (85 mm or more), with the eyes level and a neutral expression. Wide-angle selfies distort the nose by 10–20%.
2. **Cameras**: two orthographic cameras with the refs as background images. Scale each ref so chin to crown equals H, and line up the eye line at 0.5 H.

```python
import bpy
for name, rot, img in (("CamFront", (1.5708, 0, 0), "front.png"), ("CamSide", (1.5708, 0, 1.5708), "side.png")):
    cam = bpy.data.cameras.new(name); cam.type = "ORTHO"; cam.ortho_scale = 0.30
    cam.show_background_images = True
    bg = cam.background_images.new(); bg.image = bpy.data.images.load("//" + img)
    ob = bpy.data.objects.new(name, cam); ob.rotation_euler = rot
    ob.location = (0, -1, 0.12) if name == "CamFront" else (1, 0, 0.12)
    bpy.context.scene.collection.objects.link(ob)
```

3. **Match landmarks in order**: eye line, then nose base, mouth corners, chin, ear, then the outer jaw. Move whole forms with proportional editing (radius 0.02–0.04 m), never single vertices.
4. **Score**: render a black silhouette in each camera and compute the IoU against the masked ref. Targets: **front ≥ 0.90, side ≥ 0.85**. In Forge use `ref_compare(id, front, side, min_iou=0.85)`.
5. **Fix loop**: compare silhouettes, find the largest gap region, fix that one form, and re-score. Stop after 3 loops without gain; the remaining error is in the details (eyes, lips), not the silhouette.

| IoU miss | Usual cause |
|---|---|
| Side < 0.8 | skull depth or face-plane slant |
| Front < 0.85 | jaw width or cheek fat |
| Both fine but unlike | eye shape, brow height, lip thickness: check these against the landmarks |

## Done when

Both IoUs hit target, and a side-by-side `blender_get_viewport_screenshot` next to the ref shows the eye line, nose base and mouth on the same rows.

---
MIT, uefn-ducky; own words.
