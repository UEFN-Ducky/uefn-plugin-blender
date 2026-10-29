---
description: "Settle clutter with a rigid-body drop and keep the result as keys or applied transforms: convex hull shapes, mass from density, 10 substeps, 60 frames, passive ground"
metadata:
  label: "Rigid Body Drop"
---

# Rigid Body Drop

Natural piles (rocks, crates, books, loot) without hand placement.

| Setting | Value |
|---|---|
| shape | Convex Hull for props (Mesh only for the passive ground) |
| mass | volume × density: wood 600, stone 2500, metal 7800, plastic 950 kg/m³ |
| friction / bounce | 0.5-0.8 / 0-0.1 |
| world substeps / solver iterations | 10 / 10 |
| frames | 60 (2 s) is enough to settle |
| ground | Passive, Mesh shape |

```python
import bpy, bmesh
def drop(objs, ground, density=600, frames=60, to_keys=False):
    scn = bpy.context.scene
    if scn.rigidbody_world is None: bpy.ops.rigidbody.world_add()
    scn.rigidbody_world.substeps_per_frame, scn.rigidbody_world.solver_iterations = 10, 10
    scn.frame_start, scn.frame_end = 1, frames
    for o in objs + [ground]:
        bpy.context.view_layer.objects.active = o; bpy.ops.rigidbody.object_add()
    ground.rigid_body.type, ground.rigid_body.collision_shape = "PASSIVE", "MESH"
    for o in objs:
        bm = bmesh.new(); bm.from_mesh(o.data); vol = abs(bm.calc_volume()) * (o.scale.x * o.scale.y * o.scale.z); bm.free()
        o.rigid_body.collision_shape, o.rigid_body.mass = "CONVEX_HULL", max(0.01, vol * density)
        o.rigid_body.friction, o.rigid_body.restitution = 0.6, 0.05
    for f in range(1, frames + 1): scn.frame_set(f)
    for o in objs: o.select_set(True)
    bpy.ops.object.visual_transform_apply() if not to_keys else bpy.ops.rigidbody.bake_to_keyframes(frame_start=1, frame_end=frames)
    for o in objs + [ground]:
        bpy.context.view_layer.objects.active = o; bpy.ops.rigidbody.object_remove()
```

Static clutter for a game: apply the settled transforms (default) and merge non-moving pieces before export. Then run `qa-review/references/bpy-qa-score.md` for z-fighting and floating parts.

Adapted from Blender Agent Skills by EL4CTEO (simulation; MIT).
