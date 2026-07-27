# Mesh cleanup

Load before UV unwrap, baking, LOD generation, or export — and whenever shading looks blotchy, booleans fail, or UEFN import produces holes/flipped faces. Run everything through `blender_execute_blender_code`; confirm visually with `blender_get_viewport_screenshot`.

## Cleanup order (order matters)

| Step | Action | Why this order |
|---|---|---|
| 1 | Apply rotation + scale | Every threshold below is in meters; unapplied scale makes them wrong |
| 2 | Merge by distance | Collapses duplicate verts so later checks see real topology |
| 3 | Dissolve degenerate | Merging can leave zero-area faces / zero-length edges |
| 4 | Delete loose + interior faces | Dead geometry breaks manifold checks and inflates exports |
| 5 | Non-manifold repair | Fill holes, kill wire edges, split >2-face edges |
| 6 | Recalculate normals outside | Only meaningful once the shell is manifold |
| 7 | Shading (smooth + sharp edges) | Last — depends on final topology |
| 8 | `mesh.validate()` | Safety net for corrupt custom data |

Save a checkpoint first: `bpy.ops.wm.save_mainfile()` — steps 2–5 are destructive.

## Inspect report — run this FIRST and after each fix

```python
import bpy, bmesh

EPS_LEN, EPS_AREA = 1e-6, 1e-8   # meters / square meters

def cleanup_report(obj):
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)                      # object mode; in edit mode use bmesh.from_edit_mesh
    loose_verts = [v for v in bm.verts if not v.link_edges]
    wire_edges  = [e for e in bm.edges if not e.link_faces]
    boundary    = [e for e in bm.edges if e.is_boundary]
    multi_face  = [e for e in bm.edges if len(e.link_faces) > 2]
    nm_verts    = [v for v in bm.verts if not v.is_manifold]
    zero_edges  = [e for e in bm.edges if e.calc_length() < EPS_LEN]
    zero_faces  = [f for f in bm.faces if f.calc_area() < EPS_AREA]
    tris  = sum(1 for f in bm.faces if len(f.verts) == 3)
    quads = sum(1 for f in bm.faces if len(f.verts) == 4)
    ngons = len(bm.faces) - tris - quads
    closed = not boundary and not wire_edges
    inverted = closed and bm.calc_volume(signed=True) < 0   # whole shell inside-out
    s = obj.scale
    print(f"=== {obj.name} ===")
    print(f"verts {len(bm.verts)}  edges {len(bm.edges)}  faces {len(bm.faces)}")
    print(f"tris {tris}  quads {quads}  ngons {ngons}")
    print(f"loose verts {len(loose_verts)}  wire edges {len(wire_edges)}")
    print(f"boundary edges {len(boundary)} ({'closed shell' if closed else 'OPEN'})")
    print(f"non-manifold: edges>2faces {len(multi_face)}  verts {len(nm_verts)}")
    print(f"degenerate: zero-len edges {len(zero_edges)}  zero-area faces {len(zero_faces)}")
    print(f"shell inverted: {inverted}")
    print(f"scale {tuple(round(v,4) for v in s)}  rot {tuple(round(v,4) for v in obj.rotation_euler)}")
    if s.x * s.y * s.z < 0:
        print("WARNING: negative scale — applying it will flip normals")
    bm.free()

for ob in bpy.context.selected_objects:
    if ob.type == 'MESH':
        cleanup_report(ob)
```

All counts should be 0 (except tris/quads/ngons and, for intentionally open meshes, boundary edges) before export.

## 1. Apply rotation and scale

```python
import bpy
ob = bpy.context.active_object
with bpy.context.temp_override(object=ob, active_object=ob, selected_editable_objects=[ob]):
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
```

- Leave location alone unless the pivot is wrong — UEFN uses object origin as the pivot.
- Negative scale (mirrored object) flips normals when applied: recalc normals (step 6) afterwards.
- Multi-user mesh data blocks make `transform_apply` fail — run `ob.data = ob.data.copy()` first if needed.

## 2. Merge by distance

```python
import bpy, bmesh
ob = bpy.context.active_object
me = ob.data
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)   # = UI "Merge by Distance"
bm.to_mesh(me); bm.free(); me.update()
```

Thresholds: `0.0001` (0.1 mm) for authored geometry; `0.001`–`0.01` for imported/scanned/CAD meshes — inspect the report between attempts, a too-big threshold welds detail shut.

## 3–4. Degenerate, loose, interior faces

```python
import bpy
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.dissolve_degenerate(threshold=0.0001)          # zero-area faces, zero-len edges
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.delete_loose(use_verts=True, use_edges=True, use_faces=False)
bpy.ops.mesh.select_mode(type='FACE')
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.mesh.select_interior_faces()
bpy.ops.mesh.delete(type='FACE')                            # interior faces = bake/AO poison
bpy.ops.object.mode_set(mode='OBJECT')
```

`select_interior_faces` is a heuristic — on a mesh with intentional internal walls (hollow props), screenshot the selection before deleting instead of trusting it blind.

## 5. Non-manifold: detect and repair

Detection for eyeballing (leaves the problem edges selected — screenshot it):

```python
import bpy
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_mode(type='EDGE')
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.mesh.select_non_manifold(extend=False, use_wire=True, use_boundary=True,
                                 use_multi_face=True, use_non_contiguous=True, use_verts=True)
bpy.ops.object.mode_set(mode='OBJECT')
```

Scripted repair via bmesh:

```python
import bpy, bmesh
ob = bpy.context.active_object
bm = bmesh.new(); bm.from_mesh(ob.data)
wire = [e for e in bm.edges if not e.link_faces]
bmesh.ops.delete(bm, geom=wire, context='EDGES')
loose = [v for v in bm.verts if not v.link_edges]
bmesh.ops.delete(bm, geom=loose, context='VERTS')
holes = [e for e in bm.edges if e.is_boundary]
bmesh.ops.holes_fill(bm, edges=holes, sides=8)              # sides=0 = fill any hole size
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)           # consistent outward winding
bm.to_mesh(ob.data); bm.free(); ob.data.update()
```

Edges with >2 faces (T-junctions from bad booleans) can't be auto-filled — delete the offending sliver faces (`f` for `f in e.link_faces` with smallest `calc_area()`) or redo the boolean with the Exact solver. If the mesh is beyond hand-repair, voxel remesh is the nuclear option — see `modifiers`.

## 6. Normals: recalculate outside

```python
import bpy
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')
```

If the report says `shell inverted: True` after this, the whole shell is inside-out — run with `inside=True` once, or flip in bmesh (`bmesh.ops.reverse_faces`). Backface culling in UEFN makes inverted faces literally invisible.

## 7. Shading: smooth, flat, sharp edges

| Goal | Call |
|---|---|
| All flat (crisp low-poly) | `bpy.ops.object.shade_flat()` |
| All smooth, keep existing sharps | `bpy.ops.object.shade_smooth(keep_sharp_edges=True)` |
| Smooth + auto-sharpen by angle, baked into mesh | `bpy.ops.object.shade_smooth_by_angle(angle=0.523599, keep_sharp_edges=True)` |
| Same, but as a live modifier | `bpy.ops.object.shade_auto_smooth(use_auto_smooth=True, angle=0.523599)` |

`shade_auto_smooth` adds the "Smooth by Angle" node-group modifier — non-destructive, but it must exist (or be applied) at export time or the FBX loses the sharps. For game assets prefer `shade_smooth_by_angle`: it writes smooth shading plus the boolean `sharp_edge` edge attribute directly, nothing to forget.

Manual sharp control = write the attribute yourself:

```python
import bpy, bmesh, math
ob = bpy.context.active_object; me = ob.data
bm = bmesh.new(); bm.from_mesh(me)
hard = {e.index for e in bm.edges
        if len(e.link_faces) == 2 and e.calc_face_angle() > math.radians(30)}
bm.free()
if "sharp_edge" not in me.attributes:
    me.attributes.new("sharp_edge", 'BOOLEAN', 'EDGE')
me.attributes["sharp_edge"].data.foreach_set("value", [i in hard for i in range(len(me.edges))])
me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
me.update()
```

Edit-mode equivalent on a selection: `bpy.ops.mesh.set_sharpness_by_angle(angle=...)`. Split normals: read-only via `me.corner_normals`.

## Ngon / tri policy

| Mesh | Policy |
|---|---|
| Deforming (characters, cloth, bendables) | All quads in deforming zones; tris only in rigid/hidden areas; **zero ngons** — they deform and subdivide unpredictably |
| Static props / hard surface | Quads + tris fine; ngons acceptable only on perfectly planar faces |
| Any export to UEFN | Unreal triangulates on import anyway; add a Triangulate modifier before baking/export so YOU pick the split, not the importer — see `uefn_export` |

## 8. Final safety net: validate

```python
import bpy
me = bpy.context.active_object.data
if me.validate(verbose=True):        # True = corrupt data was repaired (details in console)
    me.update()
    print("validate() fixed corrupt data — re-run the inspect report")
```

`validate` fixes invalid loops/edges/custom-data, not design problems — it is the last step, never a substitute for steps 1–7.

## Symmetry snap (restore a drifted mirror)

For meshes that should be X-symmetric (characters, vehicles) but drifted during editing:

```python
import bpy
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
# 'NEGATIVE_X' = -X side is the source; verts within threshold snap to their mirror
bpy.ops.mesh.symmetry_snap(direction='NEGATIVE_X', threshold=0.05, factor=0.5, use_center=True)
bpy.ops.object.mode_set(mode='OBJECT')
```

If one side is outright wrong, rebuild it instead: `bpy.ops.mesh.symmetrize(direction='NEGATIVE_X', threshold=0.0001)` overwrites +X with mirrored -X.

## Version notes

- Whole workflow is identical across 4.2 LTS → 5.0. The auto-smooth property removal happened in 4.1, before this window — the `sharp_edge` attribute / Smooth by Angle modifier path is the only one that exists here.
- 5.0 renames the boolean solver enum `'FAST'` → `'FLOAT'`; only relevant if your cleanup includes redoing booleans.

## Verify

- Inspect report: all issue counts 0; `shell inverted: False`; scale `(1,1,1)`, rotation `(0,0,0)`.
- `blender_get_viewport_screenshot` in Material Preview: no black/blotchy faces (flipped normals), no shading gradients smearing across hard corners (missing sharps).
- `blender_get_object_info` on the object: poly count sane for the asset budget.

## Don'ts

- Don't touch `mesh.use_auto_smooth` / `mesh.auto_smooth_angle` — removed in 4.1; scripts using them throw `AttributeError`.
- Don't call `mesh.calc_normals_split()` — removed; split normals are automatic, read `mesh.corner_normals`.
- Don't merge-by-distance with big thresholds "to be safe" — it welds UV seams and detail shut silently.
- Don't recalc normals before fixing non-manifold geometry — the result is undefined on broken shells.
- Don't export with unapplied scale/rotation, ever; and never apply a negative scale without recalcing normals after.
- Don't skip cleanup on bake targets — interior faces and inverted shells ruin AO/normal bakes.

See also: `modifiers`, `uv_workflow`, `texture_bake`, `uefn_export`, `asset_qa`, `verify_loop`.
