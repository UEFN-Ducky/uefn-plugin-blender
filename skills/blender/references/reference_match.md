# Reference image match

Build to match a photo / concept. Lock camera + proportions before detail. Via `blender_execute_blender_code` + `blender_get_viewport_screenshot`.

## Workflow

1. Import reference (Empty Image / background / plane).
2. Analyze: silhouette, proportions, materials, implied scale.
3. Rough camera match if the ref is a photo.
4. `blockout` → discipline subskill → detail.
5. Screenshot compare → iterate.
6. Pass checklist → `asset_qa`.

## Load reference

```python
import bpy
bpy.ops.object.empty_add(type='IMAGE', location=(0, -2, 1))
empty = bpy.context.active_object
empty.name = "REF_Concept"
empty.empty_display_size = 2.0
# Assign image
img = bpy.data.images.load(r"C:\path\ref.png", check_existing=True)
empty.data = img
```

Or a textured plane facing the camera for side-by-side modeling.

## Camera / view discipline

- Match focal length roughly if known.
- Keep one orthographic side/front for proportion locks.
- Don't chase pixels until blockout silhouette matches.

## Compare loop

```python
# After each major pass:
# 1. blender_get_viewport_screenshot
# 2. Compare silhouette landmarks to REF
# 3. Fix proportions BEFORE materials/detail
```

## Checklist

- [ ] Overall proportions
- [ ] Major landmarks aligned
- [ ] Material read (metal / cloth / paint)
- [ ] No invented features the user didn't ask for
- [ ] Scale in meters believable vs human/door refs

## Don'ts

- Don't detail before camera/proportions lock.
- Don't ignore the reference and "improve" the design unless asked.
- Don't model from a single foreshortened photo without side checks.

Next: route to `hard_surface` / `organic_forms` / `face_topology` / etc. → `verify_loop`.
