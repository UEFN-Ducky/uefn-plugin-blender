# Pivots, grounding and weld-before-check

## Pivot without moving the object

Move the mesh data, then the object by the same world offset. `bottom` = base centre (props), `center`, `corner` = min corner (modular kits on a grid). `ground=True` drops the lowest point to z = 0 (imports often float or sink).

```python
import bpy
from mathutils import Matrix, Vector

def set_origin(ob, at="bottom", ground=False):
    vs = [v.co for v in ob.data.vertices]
    lo = Vector([min(v[i] for v in vs) for i in range(3)]); hi = Vector([max(v[i] for v in vs) for i in range(3)])
    mid = (lo + hi) / 2
    pivot = {"bottom": Vector((mid.x, mid.y, lo.z)), "center": mid, "corner": lo}[at]
    ob.data.transform(Matrix.Translation(-pivot)); ob.data.update()
    ob.matrix_world = Matrix.Translation(ob.matrix_world.to_3x3() @ pivot) @ ob.matrix_world
    if ground:
        ob.location.z -= min((ob.matrix_world @ v.co).z for v in ob.data.vertices)
    return f"{ob.name}: origin {at}, location {tuple(round(c, 3) for c in ob.location)}"

bpy.ops.mesh.primitive_cube_add(size=2, location=(1, 2, 3))
print(set_origin(bpy.context.active_object, "corner", ground=True))
```

Imports: also normalise scale from the bounding box (a 2 m door imported as 200 m means a cm/m mix-up: scale by 0.01, then apply scale).

## Weld before counting non-manifold edges

FBX/glTF exporters split vertices at UV seams and hard edges, so a re-imported mesh shows hundreds of "open" edges that are only seams. Merge by distance first, then count.

```python
import bpy, bmesh

def manifold_report(ob, weld=1e-5):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    before = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=weld)
    open_edges = sum(1 for e in bm.edges if len(e.link_faces) != 2)
    welded = before - len(bm.verts); bm.free()  # report only: ob.data is unchanged
    return f"{ob.name}: welded {welded}, open edges {open_edges}"

print(manifold_report(bpy.context.active_object))
```

**Done when:** every kit piece reports `open edges 0` after the weld, and a top render shows pieces meeting edge to edge on the grid with their pivots on the min corner.

---
Adapted from Blender Agent Skills (blender-core scene setup) by EL4CTEO, MIT licence. Same as Forge `origin(at, ground)`.
