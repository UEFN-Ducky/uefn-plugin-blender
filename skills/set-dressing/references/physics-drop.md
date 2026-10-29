# Physics drop for natural clutter

Place props a little above their resting surface, simulate, keep the final pose. Clutter that fell looks placed by gravity, not by a grid. Run in one `blender_execute_blender_code` call.

| Setting | Value |
|---|---|
| movers | Active, shape Convex Hull, margin 0.001 m |
| surfaces | Passive, shape Mesh |
| world | substeps 10, solver iterations 10 |
| frames | 60 (30 for a few small items) |
| mass | leave 1 kg unless items stack: then density x volume |

```python
import bpy

def drop(movers, surfaces, frames=60):
    scene = bpy.context.scene
    if scene.rigidbody_world is None:
        bpy.ops.rigidbody.world_add()
    world = scene.rigidbody_world
    if world.collection is None:
        world.collection = bpy.data.collections.new("RigidBodyWorld")
    world.substeps_per_frame, world.solver_iterations = 10, 10
    world.point_cache.frame_start, world.point_cache.frame_end = 1, frames
    for ob, kind in [(o, "ACTIVE") for o in movers] + [(o, "PASSIVE") for o in surfaces]:
        if ob.name not in world.collection.objects:
            world.collection.objects.link(ob)
        ob.rigid_body.type = kind
        ob.rigid_body.collision_shape = "CONVEX_HULL" if kind == "ACTIVE" else "MESH"
        ob.rigid_body.collision_margin = 0.001
    for f in range(1, frames + 1):
        scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    final = {o: o.evaluated_get(dg).matrix_world.copy() for o in movers}
    for o in list(movers) + list(surfaces):  # bake: drop the bodies, keep the landed transforms
        world.collection.objects.unlink(o)
    for o, m in final.items():
        o.matrix_world = m
    scene.frame_set(1)
    return ", ".join(f"{o.name} z={o.matrix_world.translation.z:.3f}" for o in movers)

bpy.ops.mesh.primitive_plane_add(size=10); floor = bpy.context.active_object
bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 0, 2)); box = bpy.context.active_object
print(drop([box], [floor], 50))
```

**Done when:** a side render shows every item touching its surface (no gaps, no interpenetration) and the printed z values sit at half each item's height above the surface.

Merge the settled clutter into one mesh per cluster for game export (see `story-clusters.md`).

---
Adapted from Blender Agent Skills (physics) by EL4CTEO, MIT licence. Same settle as Forge `drop`.
