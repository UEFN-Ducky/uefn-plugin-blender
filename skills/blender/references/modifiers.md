# Modifiers

Load when adding, configuring, ordering, or applying modifiers via bpy: the 4.x modifier stack playbook (Bevel, Boolean, Mirror, Subdiv, Array, Solidify, Shrinkwrap, Data Transfer, Weld, Triangulate, Decimate, Remesh, Lattice/SimpleDeform, Smooth by Angle) plus apply-before-export rules.

## Stack ordering (top evaluates first)

Canonical hard-surface order — deviate only with a reason:

| # | Slot | Modifiers | Why |
|---|------|-----------|-----|
| 1 | Symmetry | Mirror | everything downstream stays symmetric |
| 2 | Duplication | Array | duplicates inherit later edits |
| 3 | Cuts | Boolean(s) | cut before bevel so seams get beveled |
| 4 | Thickness | Solidify | shell after cuts, before edge treatment |
| 5 | Edges | Bevel, Weld | Weld fuses near-coincident verts Boolean/Mirror left behind |
| 6 | Smoothing | Subdivision Surface | creases control tightness |
| 7 | Deforms | Lattice, SimpleDeform, Shrinkwrap, Armature | deform the *generated* result |
| 8 | Shading | Smooth by Angle, Weighted Normal, Data Transfer (normals) | shading is always last |
| 9 | Export-only | Triangulate, Decimate | add late, often let the exporter handle it |

```python
import bpy, math
obj = bpy.data.objects["SM_Crate"]
mod = obj.modifiers.new(name="Bevel", type='BEVEL')   # always name explicitly
# Reorder without ops:
obj.modifiers.move(obj.modifiers.find("Bevel"), 0)     # index-based, no context needed
```

## Bevel

```python
b = obj.modifiers.new("Bevel", 'BEVEL')
b.width = 0.008                    # meters; game-asset bevels: 2–10 mm reads well in UEFN
b.segments = 2                     # 1–2 for realtime; more only if baking from this
b.limit_method = 'ANGLE'
b.angle_limit = math.radians(40)   # only edges sharper than 40° get beveled
b.use_clamp_overlap = True         # stops bevels colliding on thin geometry
b.harden_normals = True            # fakes extra segments via custom normals
b.miter_outer = 'MITER_ARC'        # cleaner 3-way corners
```

`harden_normals` needs the object shaded smooth — run `bpy.ops.object.shade_smooth()` on it first and keep the shading step (Smooth by Angle) *below* the Bevel. Use `limit_method='WEIGHT'` + the `bevel_weight_edge` edge attribute when angle limiting picks up unwanted edges.

## Boolean

```python
cut = bpy.data.objects["cutter"]
bl = obj.modifiers.new("Bool_cut", 'BOOLEAN')
bl.operation = 'DIFFERENCE'        # or 'UNION' / 'INTERSECT'
bl.object = cut                    # operand_type='COLLECTION' + bl.collection for many cutters
bl.solver = 'EXACT'                # robust; 5.0 renamed the fast solver 'FAST' -> 'FLOAT'
bl.use_self = False                # True only if the cutter self-intersects (slower)
bl.use_hole_tolerant = True        # tolerate open/non-watertight operands
cut.display_type = 'WIRE'; cut.hide_render = True   # keep cutter visible-but-unobtrusive
```

Failure triage, in order:
1. **Nothing happens** — cutter doesn't actually intersect, or it's the wrong operand; check with `blender_get_object_info`.
2. **Faces vanish / inside-out result** — flipped normals: in Edit Mode `bpy.ops.mesh.normals_make_consistent(inside=False)` on both meshes.
3. **Artifacts on coplanar faces** — EXACT hates perfectly coplanar overlap; nudge the cutter 0.1–1 mm so faces interpenetrate.
4. **Open cutter leaks** — set `use_hole_tolerant=True`, or Solidify the cutter so it's a closed volume.
5. **Slow** — FAST (`'FLOAT'` in 5.0) is fine for blockouts; switch back to EXACT before applying.

After applying a Boolean, run a Weld or bmesh cleanup — see `mesh_cleanup`.

## Mirror

```python
m = obj.modifiers.new("Mirror", 'MIRROR')
m.use_axis = (True, False, False)          # +X/-X symmetry (object-local)
m.use_bisect_axis = (True, False, False)   # cut off geometry crossing the plane first
m.use_bisect_flip_axis = (False, False, False)  # flip which half survives
m.use_clip = True                          # verts can't cross the mirror plane while editing
m.use_mirror_merge = True; m.merge_threshold = 0.001
# m.mirror_object = bpy.data.objects["pivot"]  # mirror across another object's axes
```

Bisect+clip is the fix for "double geometry at the seam": it trims overhang, then merge welds the center line.

## Subdivision Surface + creases

```python
s = obj.modifiers.new("Subdiv", 'SUBSURF')
s.levels = 2; s.render_levels = 2
s.use_creases = True
# Edge creases are a float EDGE attribute since 4.0 (MeshEdge.crease is gone):
me = obj.data
ca = me.attributes.get("crease_edge") or me.attributes.new("crease_edge", 'FLOAT', 'EDGE')
for e in me.edges:
    if abs(me.vertices[e.vertices[0]].co.z - me.vertices[e.vertices[1]].co.z) < 1e-6:
        ca.data[e.index].value = 1.0       # crease = 1.0 -> fully sharp under subdiv
```

For game assets keep levels ≤ 2 and treat Subdiv as a bake source, not export geometry — see `lod_collision`.

## Array

```python
a = obj.modifiers.new("Array", 'ARRAY')
a.count = 6
a.use_relative_offset = True
a.relative_offset_displace = (1.0, 0.0, 0.0)   # 1.0 = one bounding-box width apart
# Constant spacing instead:
a.use_constant_offset = True; a.constant_offset_displace = (0.0, 0.0, 0.5)
# Radial array: offset by an empty's transform (rotate the empty N degrees)
emp = bpy.data.objects.new("radial_pivot", None); bpy.context.collection.objects.link(emp)
emp.rotation_euler[2] = math.radians(360 / a.count)
a.use_object_offset = True; a.offset_object = emp
a.use_merge_vertices = True; a.merge_threshold = 0.001   # weld touching copies
# a.fit_type = 'FIT_LENGTH'; a.fit_length = 5.12          # fill one 512uu UEFN tile
```

Object-offset arrays evaluate in the empty's space — keep the empty at the mesh origin for clean radials.

## Solidify

```python
so = obj.modifiers.new("Solidify", 'SOLIDIFY')
so.thickness = 0.02                # meters; positive = along normals
so.offset = -1.0                   # -1 keeps original surface as the outer shell
so.use_even_offset = True          # constant thickness at sharp corners
so.use_rim = True                  # cap the open edges
```

Use on planar cards, pipes, and to make open cutters watertight for Booleans.

## Shrinkwrap

```python
sw = obj.modifiers.new("Shrinkwrap", 'SHRINKWRAP')
sw.target = bpy.data.objects["SM_Sculpt"]
sw.wrap_method = 'PROJECT'         # 'NEAREST_SURFACEPOINT' for cloth-on-body offsets
sw.use_negative_direction = True
sw.wrap_mode = 'ON_SURFACE'
sw.offset = 0.002                  # tiny gap prevents z-fighting
# sw.vertex_group = "wrap_zone"    # limit influence
```

Primary uses: retopo mesh conformed to a sculpt (`retopology`), clothing snapped over a body (`character_clothing`).

## Data Transfer

```python
dt = lowpoly.modifiers.new("NormalXfer", 'DATA_TRANSFER')
dt.object = donor                      # clean, smooth-shaded source
dt.use_loop_data = True
dt.data_types_loops = {'CUSTOM_NORMAL'}
dt.loop_mapping = 'POLYINTERP_NEAREST'
# Weights instead: dt.use_vert_data = True; dt.data_types_verts = {'VGROUP_WEIGHTS'}
```

Custom-normal transfer is the trick for clean shading on decimated or hand-built lowpolys. Put it last in the stack (after everything that changes topology).

## Cleanup / export set

```python
w = obj.modifiers.new("Weld", 'WELD'); w.merge_threshold = 0.0005; w.mode = 'ALL'
t = obj.modifiers.new("Tri", 'TRIANGULATE'); t.quad_method = 'SHORTEST_DIAGONAL'; t.keep_custom_normals = True
d = obj.modifiers.new("Decimate", 'DECIMATE'); d.decimate_type = 'COLLAPSE'; d.ratio = 0.5
# d.decimate_type = 'DISSOLVE'; d.angle_limit = math.radians(5)  # planar cleanup, keeps UVs better
r = obj.modifiers.new("Remesh", 'REMESH'); r.mode = 'VOXEL'; r.voxel_size = 0.02
```

One-shot voxel remesh without a modifier (op takes no params — configure the mesh first):

```python
obj.data.remesh_voxel_size = 0.02
obj.data.use_remesh_preserve_volume = True
with bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj]):
    bpy.ops.object.voxel_remesh()
```

Remesh destroys UVs and vertex groups — it belongs before UVs/skinning, never after.

## Lattice / SimpleDeform (non-destructive shaping)

```python
lat = bpy.data.lattices.new("LAT_bend"); lat.points_u = lat.points_v = 2; lat.points_w = 3
lat_ob = bpy.data.objects.new("LAT_bend", lat); bpy.context.collection.objects.link(lat_ob)
lat_ob.location = obj.location; lat_ob.scale = obj.dimensions          # rough fit around target
lm = obj.modifiers.new("Lattice", 'LATTICE'); lm.object = lat_ob
lat.points[8].co_deform.x += 0.2        # push control points to deform

sd = obj.modifiers.new("Bend", 'SIMPLE_DEFORM')
sd.deform_method = 'BEND'               # 'TWIST' / 'TAPER' / 'STRETCH'
sd.angle = math.radians(45); sd.deform_axis = 'Z'
# sd.origin = pivot_empty               # empty controls the bend center/axis
```

## Smooth by Angle (the auto-smooth replacement)

`mesh.use_auto_smooth` / `auto_smooth_angle` were removed in 4.1. Modern options:

```python
# A) Live node-group modifier "Smooth by Angle" (bundled asset):
with bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj]):
    bpy.ops.object.shade_auto_smooth(angle=math.radians(30))
sm = obj.modifiers["Smooth by Angle"]
sm["Input_1"] = math.radians(45)        # Angle socket (identifier "Input_1")
sm["Socket_1"] = False                  # Ignore Sharpness
obj.update_tag(); bpy.context.view_layer.update()

# B) Bake it — no modifier; writes smooth shading + the boolean 'sharp_edge' edge attribute:
with bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj]):
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(30), keep_sharp_edges=True)
```

Prefer (B) for export-ready meshes (deterministic normals, one less modifier); (A) while iterating. Keep it below Bevel/Boolean in the stack.

## Applying modifiers (context requirements)

`bpy.ops.object.modifier_apply` runs in **Object Mode only**, on the **active object**, and **fails on multi-user mesh data** unless `single_user=True`:

```python
def apply_mod(obj, mod_name):
    with bpy.context.temp_override(object=obj, active_object=obj,
                                   selected_objects=[obj], selected_editable_objects=[obj]):
        bpy.ops.object.modifier_apply(modifier=mod_name, single_user=True)
apply_mod(obj, "Bool_cut")
# Or skip ops entirely for whole-stack flattening:
dg = bpy.context.evaluated_depsgraph_get()
obj.data = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))  # replaces mesh; clears stack yourself
obj.modifiers.clear()
```

Most modifiers refuse to apply on meshes with shape keys — apply before adding shape keys, or use the depsgraph route on a shape-key-free duplicate. Save first: `bpy.ops.wm.save_mainfile()`.

## Apply before export vs keep live

| Apply destructively (before UVs/bake) | Keep live until export |
|---|---|
| Boolean, Remesh, Decimate, Solidify | Triangulate (exporter can apply) |
| Mirror — if you need asymmetric UVs/paint | Mirror — if symmetric UVs are fine |
| Array — if instances need unique texel space | Bevel, Subdiv, Smooth by Angle (exporter applies) |
| Weld after Booleans | Deforms driven by Lattice/empties you still tweak |

FBX/glTF exporters apply remaining modifiers for static meshes; for skeletal meshes with shape keys they cannot — flatten manually first. Full recipes: `uefn_export`, `skeletal_export`.

## Version notes

- All snippets run unchanged on 4.2 LTS → 4.5 LTS.
- 5.0: Boolean solver enum `'FAST'` → `'FLOAT'` (`'EXACT'` unchanged). 5.0 also ships new geometry-nodes-based modifiers (Array, Scatter on Surface, …); this file's snippets target the classic modifiers, which is fine on 4.x.
- Since 4.0: edge creases/bevel weights are attributes (`crease_edge`, `bevel_weight_edge`), not `MeshEdge` properties; the positional context-dict for ops is gone — use `temp_override`.

## Verify

- `blender_get_object_info` after each add/apply: confirm the modifier list, order, and post-apply poly counts (`len(obj.data.polygons)` before vs after Decimate/Remesh).
- `blender_get_viewport_screenshot` after Boolean/Bevel: look for black shading splotches (bad normals), unbeveled seam edges, cutter still visible as solid.
- After Boolean apply: non-manifold check via `mesh_cleanup` before moving on.
- Mirror: screenshot head-on to the mirror plane — no doubled silhouette or seam crack at center.

## Don'ts

- Don't touch `mesh.use_auto_smooth` / `mesh.auto_smooth_angle` — removed in 4.1; use Smooth by Angle / `shade_smooth_by_angle`.
- Don't call `modifier_apply` in Edit Mode, on a non-active object, or on shared mesh data without `single_user=True`.
- Don't apply Subdiv to export geometry — it's a bake source; export the low-poly.
- Don't leave Boolean cutters renderable or exportable — `display_type='WIRE'`, `hide_render=True`, park them in a `COL_cutters` collection.
- Don't Triangulate early — keep quads for editing/UVs; triangulate last or let the exporter do it.
- Don't Remesh after UV unwrapping or skinning — it wipes both.
- Don't stack Weld above Mirror with clipping — it can eat the center seam before the mirror merge runs.

See also: `mesh_cleanup`, `hard_surface`, `geometry_nodes`, `lod_collision`, `uefn_export`, `verify_loop`.
