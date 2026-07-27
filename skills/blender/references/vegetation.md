# Vegetation

Trees, plants, grass — game-friendly cards and simple trunks for UEFN density. Origin at ground contact. Via `blender_execute_blender_code`.

## Game-friendly patterns

| Part | Approach |
|---|---|
| Leaves / needles | Alpha cards / crossed planes; atlas |
| Trunk / branches | Low poly cylinders → bark bake optional |
| Grass | Card clumps; few materials |
| Scatter lookdev | `geometry_nodes` in Blender → realize before export |

Avoid full botanical leaf counts. Prefer exported mesh clusters over live GN in UEFN.

## Trunk + cards

```python
import bpy, math
# Trunk
bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=2.0, location=(0, 0, 1.0))
trunk = bpy.context.active_object
trunk.name = "SM_Tree_Trunk"
bpy.ops.object.transform_apply(scale=True)

# Leaf card
bpy.ops.mesh.primitive_plane_add(size=0.6, location=(0.4, 0, 1.8))
card = bpy.context.active_object
card.name = "SM_Tree_LeafCard"
card.rotation_euler = (math.radians(90), 0, math.radians(30))
```

Parent cards to trunk; join when shipping a single static, or keep separate for wind materials in UEFN.

## Ground origin

```python
import bpy
from mathutils import Vector
ob = bpy.data.objects["SM_Tree"]
# Lowest Z of mesh → origin
zs = [ob.matrix_world @ v.co for v in ob.data.vertices]
lowest = min(zs, key=lambda p: p.z)
bpy.context.scene.cursor.location = (ob.location.x, ob.location.y, lowest.z)
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
ob.location = (0, 0, 0)
```

## Atlas / materials

- Few materials (`MAT_Bark`, `MAT_Leaves`).
- Leaves: Principled + Alpha / clip or blend; bake if needed (`materials_shading`).
- Match texel density across kit (`uv_workflow`).

## Scatter in Blender only

Use `geometry_nodes` for lookdev density tests, then realize a **representative cluster** mesh for export — not 100k instances.

## Don'ts

- Don't export curve-hair grass or millions of unique leaves.
- Don't leave origin at trunk center (floating trees).
- Don't unique-texture every card.

Next: `materials_shading` → `lod_collision` → `uefn_export`.
