# Topology fundamentals

Why meshes shade badly, deform wrong, or bake garbage — before discipline skills.
Load when poles, n-gons, density, or "weird shading" show up. Via
`blender_execute_blender_code` + `verify_loop` screenshots.

## Goals

| Goal | Topology habit |
|------|----------------|
| Smooth shading | Even density, clean normals, sensible sharp edges |
| Deformation (characters) | Edge loops at joints; quads on bend regions |
| Baking | Low has clean UVs; high can be messy tris |
| Hard-surface mid-poly | Planar n-gons OK on flats; bevels carry the highlight |

## Quads vs tris vs n-gons

- **Quads** — default for deforming / Subsurf / organic.
- **Tris** — fine on static game meshes after export; avoid long skinny tris on curves.
- **N-gons** — OK on **flat** hard-surface faces; bad on curved deforming surfaces.

```python
import bmesh, bpy
ob = bpy.data.objects["SM_Prop"]
bm = bmesh.new(); bm.from_mesh(ob.data)
ngons = [f for f in bm.faces if len(f.verts) > 4]
tris = [f for f in bm.faces if len(f.verts) == 3]
print("ngons", len(ngons), "tris", len(tris), "faces", len(bm.faces))
bm.free()
```

## Poles (E-poles / N-poles)

- **Pole** = vertex with ≠4 edges (on a quad mesh).
- Put poles on **flat / low-deform** areas — not on elbow creases, lip corners mid-bend, or sharp ridges.
- 3- and 5-poles steer edge flow; 6+ poles usually mean "fix density."

## Edge flow rules

1. Loops follow the form (muscle, panel, lip, eyelid).
2. Joints need **ring loops** that compress/stretch (elbow, knee, finger knuckles).
3. Don't terminate a loop into a random star on a bend.
4. Support loops for Subsurf creases — or use Bevel weights for mid-poly (`hard_surface`).

Characters: `face_topology`, `body_anatomy`, `hands_feet`. Creatures: `creature_organic`.

## Density

- Dense only where silhouette or deform needs it; sparse on large flats.
- Sudden density jumps → pinching under Subsurf and ugly bakes — transition gradually.
- AI / Studio meshes: remesh or retopo — don't skin raw soup (`retopology`, `import_assets`).

## Shading bad? Checklist

1. Applied scale? (`bpy_fundamentals`)
2. Flipped normals / mixed — Face Orientation overlay (`verify_loop`)
3. Custom normals / Weighted Normal missing on mid-poly (`hard_surface`)
4. Long tris across a curve
5. N-gon on a curved surface
6. Overlapping verts — `mesh_cleanup`

## Don'ts

- Don't Subsurf a mesh full of deforming n-gons.
- Don't put poles on knuckles and call it done.
- Don't match "quad only" religiously on static mid-poly flats — planarity matters more.

Next: discipline skill → `mesh_cleanup` → `uv_workflow`.
