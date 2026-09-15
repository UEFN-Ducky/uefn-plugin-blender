# Reference image match

Build to match a photo / concept. Lock camera + proportions before detail. Via `blender_execute_blender_code` + `blender_get_viewport_screenshot`.

## Workflow

1. Fill `skill_read_subskill("blender", "reference_analysis_template")` **before** any mutate.
2. Import reference (Empty Image / background / plane).
3. Analyze: silhouette, proportions, materials, implied scale.
4. Match camera (`CAM_*` + target empty) before micro-detail.
5. `blockout` → specialist pack → detail.
6. `blender_get_viewport_screenshot` compare → gap list → fix (max 3 loops).
7. Pass checklist → `skill_read_subskill("qa-review")`.

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

Next: route to `skill_read_subskill("hard-surface")` / `organic_forms` / `skill_read_subskill("character-artist")` / etc. → `verify_loop`.
