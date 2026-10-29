---
description: "3D-print check in bpy with bmesh and BVHTree: watertight, self-intersections, zero-area faces, wall thickness (0.8 mm FDM, 0.5 mm resin), overhangs over 45 degrees, loose shells and volume; STL export in millimetres"
metadata:
  label: "3D Print Check"
---

# 3D Print Check

| Check | Fail when | Fix |
|---|---|---|
| watertight | any boundary or non-manifold edge | fill holes, voxel remesh |
| self-intersection | `BVHTree.overlap(self)` not empty | voxel remesh 0.5-1 % of height, boolean union |
| zero-area | face area < 1e-8 m² | dissolve degenerate |
| thin wall | inward ray hits within 0.8 mm (FDM) / 0.5 mm (resin) | Solidify, thicken |
| overhang | > 10 % of area faces down more than 45° (not on the bed) | rotate, supports |
| shells | more loose parts than intended | join + union |

```python
import bpy, bmesh, math
from mathutils.bvhtree import BVHTree

def print_check(obj, min_wall=0.0008, overhang=45):
    bm = bmesh.new(); bm.from_mesh(obj.data); bm.transform(obj.matrix_world); bm.normal_update()
    tree = BVHTree.FromBMesh(bm)
    low = min(v.co.z for v in bm.verts); c = math.cos(math.radians(overhang))
    thin = sum(tree.ray_cast(f.calc_center_median() - f.normal * 1e-6, -f.normal, min_wall)[0] is not None
               for f in bm.faces if f.calc_area() > 1e-12)
    down = sum(f.calc_area() for f in bm.faces if f.normal.z < -c and min(v.co.z for v in f.verts) > low + 1e-4)
    area = sum(f.calc_area() for f in bm.faces) or 1
    out = {"open": sum(e.is_boundary for e in bm.edges),
           "nonmanifold": sum(not e.is_manifold and not e.is_boundary for e in bm.edges),
           "intersect": len({i for p in tree.overlap(tree) for i in p}), "thin": thin,
           "overhang_pct": round(100 * down / area, 1), "volume_cm3": round(bm.calc_volume() * 1e6, 1)}
    bm.free(); return out
```

Export: `bpy.ops.wm.stl_export(filepath=..., export_selected_objects=True, global_scale=1000.0, forward_axis="Y", up_axis="Z")` writes millimetres (scene in metres). Model at real size: a 10 cm figure is 0.1 m. Same checks as Forge `print_check`.

Adapted from AgentPMT Blender 3D Modeling (3D-print checks; feature list only) and HoldMyBeer-gg/blenderwright (print checks; MIT).
