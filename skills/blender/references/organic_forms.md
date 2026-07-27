# Organic forms

Soft-volume modeling WITHOUT interactive sculpting: creatures, bodies, fruit, cushions, rocks, tentacles, branches. Everything here is deterministic bpy — no brush strokes. Load when the shape is curved/lumpy/alive; for crisp mechanical shapes load `hard_surface`.

## Technique picker

| Target form | Technique | Section |
|---|---|---|
| Rounded masses (torso, fruit, cushion, boulder) | Subsurf cage + crease control | Massing |
| Local bumps/dents/pulls (brow, belly, dent) | Proportional-edit transforms | Grab brush |
| Limbs, tails, tentacles, horns, tree branches | Skin modifier over an edge spine | Skin |
| Blobbify a boxy mass toward sphere/pill | Cast modifier | Deformers |
| Global squash, bulge, taper on a finished mesh | Lattice modifier | Deformers |
| Bend a long mesh along a path (tail, vine, snake) | Curve modifier | Deformers |
| Fuse separate masses into one watertight blob | Voxel remesh + smooth pass | Fuse & relax |
| Skin pores, wrinkles, believable micro-detail | Escalate | Escalation |

Work in meters at real-world size (UEFN character ≈ 1.9 m tall; the exporter handles the cm conversion — `uefn_export`).

## Massing with subdivision surfaces

Keep the cage coarse (8–60 verts per mass) — you shape the cage, Subsurf makes it organic. `bpy.data`-first:

```python
import bpy
ob = bpy.context.active_object            # a cube/blockout mass from `blockout`
sub = ob.modifiers.new("Subdiv", 'SUBSURF')
sub.levels = 2                            # viewport; keep render_levels equal for parity
sub.render_levels = 2
bpy.ops.object.shade_smooth()
```

Hold a feature (lip of a mouth, rim of a mushroom cap) with edge creases instead of extra loops — creases are the generic `crease_edge` attribute (the old `MeshEdge.crease` property is gone since 4.0):

```python
me = ob.data
ce = me.attributes.get("crease_edge") or me.attributes.new("crease_edge", 'FLOAT', 'EDGE')
for ei in (4, 5, 6, 7):                   # edge indices to hold
    ce.data[ei].value = 0.8               # 0..1; 1.0 = razor sharp under Subsurf
```

Rule: if the silhouette needs a new lobe, add cage geometry (`bpy.ops.mesh.loop_cut_slide` is interactive-ish; prefer `bpy.ops.mesh.subdivide` on a selection, or extrude region) — don't crank `levels` past 3.

## Proportional editing — the scriptable grab brush

`bpy.ops.transform.*` ops take proportional-edit kwargs directly. Select a vert cluster, transform with a falloff radius — this is the deterministic replacement for sculpt Grab/Inflate.

```python
import bpy
ob = bpy.data.objects["SM_Creature"]
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
bpy.ops.object.mode_set(mode='OBJECT')    # vertex.select writes only apply in object mode
me = ob.data
for v in me.vertices:
    v.select = (v.co.z > 1.5 and v.co.y < 0.0)   # e.g. brow region
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.transform.translate(
    value=(0.0, -0.06, 0.02),
    use_proportional_edit=True,
    proportional_edit_falloff='SMOOTH',   # 'SPHERE' rounder, 'SHARP' pinches, also
                                          # 'ROOT'|'INVERSE_SQUARE'|'LINEAR'|'CONSTANT'|'RANDOM'
    proportional_size=0.35,               # falloff radius in meters — the "brush size"
    use_proportional_connected=True)      # topological falloff: won't grab the other arm
bpy.ops.object.mode_set(mode='OBJECT')
```

- Inflate = `bpy.ops.transform.resize(value=(1.2, 1.2, 1.2), ...)` with the same kwargs; twist = `bpy.ops.transform.rotate(value=0.3, orient_axis='Z', ...)`.
- Several small pulls beat one big one; screenshot between pulls (`verify_loop`).
- Falloff radius is in Blender units (m), independent of selection size.

## Skin modifier — limbs, tails, branches

Draw the skeleton as verts+edges, let Skin wrap a quad tube around it, Subsurf smooths. Per-vertex radii sculpt the taper.

```python
import bpy, bmesh
me = bpy.data.meshes.new("Limb")
ob = bpy.data.objects.new("SM_Limb", me)
bpy.context.collection.objects.link(ob)
bm = bmesh.new()
pts = [(0, 0, 0), (0, 0, 0.45), (0.06, 0, 0.85), (0.16, 0, 1.10)]   # spine polyline
vs = [bm.verts.new(p) for p in pts]
for a, b in zip(vs, vs[1:]):
    bm.edges.new((a, b))
bm.to_mesh(me); bm.free()

skin = ob.modifiers.new("Skin", 'SKIN')   # adding it creates mesh.skin_vertices
skin.branch_smoothing = 0.3               # softens Y-junctions (branching trees)
sub = ob.modifiers.new("Subdiv", 'SUBSURF'); sub.levels = 2   # ALWAYS after Skin

sv = me.skin_vertices[0].data             # one entry per mesh vertex
for i, r in enumerate([0.14, 0.11, 0.07, 0.035]):   # shoulder→wrist taper, radii in m
    sv[i].radius = (r, r)                 # (rx, ry) — unequal = elliptical cross-section
sv[0].use_root = True                     # exactly one root per connected component
```

Branch by adding more edges off any spine vert before `to_mesh`. When the shape is right, apply Skin+Subsurf (`bpy.ops.object.modifier_apply(modifier=...)`, object mode, object active) and continue with proportional edits. For deforming limbs the Skin output has usable ring topology, but plan joint loop placement per `body_anatomy`.

## Cast / Lattice / Curve deformers

**Cast** — pull a subdivided mass toward a primitive; great for stylized fruit/heads from cubes:

```python
cast = ob.modifiers.new("Cast", 'CAST')
cast.cast_type = 'SPHERE'                 # 'CYLINDER' | 'CUBOID'
cast.factor = 0.6                         # 1.0 = fully projected; 0.3–0.7 keeps character
```

**Lattice** — low-resolution cage for global bulge/squash without touching topology:

```python
from mathutils import Vector
target = bpy.data.objects["SM_Creature"]
lat = bpy.data.lattices.new("LAT_bulge")
lat.points_u = lat.points_v = 2; lat.points_w = 3
lat.interpolation_type_w = 'KEY_BSPLINE'
lat_ob = bpy.data.objects.new("LAT_bulge", lat)
bpy.context.collection.objects.link(lat_ob)
bb = [Vector(c) for c in target.bound_box]
lat_ob.location = target.matrix_world @ (sum(bb, Vector()) / 8.0)   # cage on bbox center
lat_ob.scale = target.dimensions
mod = target.modifiers.new("Lattice", 'LATTICE')
mod.object = lat_ob
for p in lat.points:                      # rest coords span -0.5..0.5 per axis
    if abs(p.co.z) < 0.1:                 # middle W-slice
        p.co_deform.y += 0.15             # pot belly; offsets scale with the cage
```

**Curve** — bend tails/vines/snakes along a Bezier; model the mesh straight along one axis first:

```python
crv = bpy.data.curves.new("CRV_tail", 'CURVE'); crv.dimensions = '3D'
sp = crv.splines.new('BEZIER'); sp.bezier_points.add(1)
sp.bezier_points[0].co = (0, 0, 0); sp.bezier_points[1].co = (0, 1.5, 0.5)
for p in sp.bezier_points:
    p.handle_left_type = p.handle_right_type = 'AUTO'
crv_ob = bpy.data.objects.new("CRV_tail", crv)
bpy.context.collection.objects.link(crv_ob)
mod = ob.modifiers.new("Curve", 'CURVE')
mod.object = crv_ob
mod.deform_axis = 'POS_Y'                 # the mesh's long axis
```

Keep mesh and curve origins coincident or the bend lands offset. Animate/adjust by moving `bezier_points[i].co` — fully scriptable posing.

## Fuse & relax: remesh + smooth passes

Merge blockout masses into one watertight organic body — voxel union instead of booleans (booleans hate blobby overlaps):

```python
bpy.ops.wm.save_mainfile()                # checkpoint: remesh is destructive
bpy.ops.object.select_all(action='DESELECT')
for n in ("Body", "Head", "ArmL", "ArmR"):
    bpy.data.objects[n].select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects["Body"]
bpy.ops.object.join()
ob = bpy.context.active_object
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)  # voxel size is object-space
me = ob.data
me.remesh_voxel_size = 0.03               # ~3 cm detail on a 1.9 m creature; smaller = denser
me.use_remesh_fix_poles = True
me.use_remesh_preserve_volume = True
bpy.ops.object.voxel_remesh()             # op takes NO parameters — configure mesh props first

bpy.ops.object.mode_set(mode='EDIT')      # relax the voxel staircase
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.vertices_smooth(factor=0.5, repeat=6)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.shade_auto_smooth(angle=1.047)   # 60°; adds "Smooth by Angle" modifier (4.1+)
```

- Non-destructive variant: `RemeshModifier` with `mode='VOXEL'`, plus a `'SMOOTH'` or `'CORRECTIVE_SMOOTH'` modifier (`factor=0.6, iterations=10`) — keep live while iterating, apply before export.
- Repeat remesh→smooth→proportional-pull cycles as needed; each remesh resets topology, so do it BEFORE any UVs/weights.
- Remesh output is flow-less: fine for static props/rocks, never final topology for deforming characters — `retopology` first, and plan loops per `body_anatomy`.

## Silhouette checks

Organic forms live or die by silhouette. After every major pass: `blender_get_viewport_screenshot` from front, side, and 3/4 — the mass should read at thumbnail size; lumps that vanish in silhouette are wasted verts. Compare against reference per `reference_match`; full loop discipline in `verify_loop`. Use `blender_get_object_info` to watch vert counts — a soft prop should stay inside UEFN budgets (medium prop ≈ 3,000 verts; see `asset_qa`).

## Escalation

Escalate when deterministic tools plateau:

- **Surface detail first**: a `DisplaceModifier` with a procedural `Texture` (`direction='NORMAL'`, low `strength`) fakes skin/rock micro-relief cheaply — try before sculpting.
- **`sculpting` subskill** — Multires + mesh filters + displacement pipelines, for believable organic detail meant to be baked (`texture_bake`).
- **`sculpt_brushes` subskill** — real brush strokes (Crease Sharp, Clay, Smooth…) scripted via viewport-framed `brush_stroke`, plus masks + `mesh_filter` for brush-quality smoothing. Needs the framing/setup helpers there — don't hand-roll strokes outside it.
- **AI generation** — when the lifeform is beyond parametric assembly (realistic animal, detailed monster): `blender_generate_hyper3d_model_via_text` / `blender_generate_hyper3d_model_via_images` then `blender_poll_rodin_job_status` + `blender_import_generated_asset`; or `blender_generate_hunyuan3d_model` + `blender_poll_hunyuan_job_status` + `blender_import_generated_asset_hunyuan` (check the `*_status` tools first). Generated meshes are dense and flow-less: voxel remesh + `retopology` + `uv_workflow` before UEFN.

## Version notes

- Shading: `bpy.ops.object.shade_auto_smooth(angle=...)` adds the "Smooth by Angle" node-group modifier; `bpy.ops.object.shade_smooth_by_angle(angle=...)` writes smooth + the `sharp_edge` edge attribute with no modifier. Both exist 4.2→5.0. `mesh.use_auto_smooth` is gone since 4.1.
- If you do reach for a Boolean modifier instead of voxel union: the fast-solver enum is `'FAST'` in 4.2–4.5 and renamed `'FLOAT'` in 5.0 (`'EXACT'` unchanged).
- Everything else above (proportional kwargs, Skin/Cast/Lattice/Curve props, voxel remesh props) is stable across 4.2 LTS → 5.0.

## Verify

- Screenshot front/side/3-quarter: silhouette reads at thumbnail size, no accidental lumps or flat spots.
- `blender_get_object_info`: vert count within budget; scale is (1,1,1) after `transform_apply`.
- Even polygon density — no long thin triangles, no dense-patch/sparse-patch seams (zoom a screenshot on transitions).
- Wireframe sanity after remesh: watertight, no floating shrapnel (`mesh_cleanup` if in doubt).
- For deforming assets: joint areas have (or will get, via `retopology`) real loops.

## Don'ts

- Don't touch `mesh.use_auto_smooth` / `auto_smooth_angle` — removed in 4.1; use the shade ops above.
- Don't hand-roll `bpy.ops.sculpt.brush_stroke` or dyntopo here — proportional transforms first; if you need real brushes, load `sculpt_brushes` (it has the required viewport framing).
- Don't voxel-remesh with unapplied scale — `remesh_voxel_size` is object-space and the density will be wrong.
- Don't remesh after UVs, vertex groups, or shape keys exist — it destroys them; remesh early.
- Don't put Subsurf before Skin in the stack — Skin needs the raw spine edges.
- Don't crank Subsurf `levels` above 3 to fix a bad cage — fix the cage.
- Don't ship remeshed/AI-generated flow-less topology as a deforming character — `retopology` first.

See also: `blockout`, `modifiers`, `sculpting`, `retopology`, `body_anatomy`, `creature_organic`, `verify_loop`, `mesh_cleanup`, `asset_qa`, `uefn_export`.
