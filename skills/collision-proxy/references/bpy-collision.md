# Ducky bpy — collision proxies

Run snippets via `blender_execute_blender_code`. Naming/recipes: this pack's other references. UEFN ship: `skill_read_subskill("blender", "uefn_export")`.

# Collision proxies


Prefer boxes / capsules / simple convex pieces over direct mesh collision.

```python
import bpy
# Box proxy around bounds
ob = bpy.data.objects["SM_Prop"]
# Duplicate bounds as cube
from mathutils import Vector
coords = [ob.matrix_world @ v.co for v in ob.data.vertices]
min_c = Vector(map(min, zip(*coords)))
max_c = Vector(map(max, zip(*coords)))
center = (min_c + max_c) / 2
size = max_c - min_c
bpy.ops.mesh.primitive_cube_add(location=center)
proxy = bpy.context.active_object
proxy.name = "UCX_SM_Prop"          # UE-friendly prefix if using UCX convention
proxy.scale = size / 2
bpy.ops.object.transform_apply(scale=True)
proxy.display_type = 'WIRE'
```

Multiple convex pieces: `UCX_SM_Prop_01`, `_02`, … Export with mesh or let UEFN rebuild — still provide sensible proxies for gameplay.

## Don'ts

- Don't Decimate without applied scale.
- Don't keep boolean cutters / Multires on LOD exports.
- Don't use render mesh as collision for complex shapes.

Next: `skill_read_subskill("qa-review")` → `uefn_export`.
