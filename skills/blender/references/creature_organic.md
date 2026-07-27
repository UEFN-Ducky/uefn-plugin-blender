# Creatures & non-human characters

Quadrupeds, monsters, dragons, tentacled things: adapting joint/loop rules built for bipeds to non-human anatomy, and turning generated or sculpted blobs into skinnable game meshes. For human bodies see `body_anatomy`; for humanoid faces see `face_topology`.

## Budgets scale with silhouette importance

Spend polygons where the silhouette changes — head, horns, wing fingers, tail curve, limb outlines. Interior mass (belly, flanks, back) reads from shading and stays cheap. Skinned meshes get no Nanite benefit in UEFN, so these are real budgets and LODs are mandatory (`lod_collision`).

| Tier | Examples | LOD0 tris (guide) | Cut corners on |
|---|---|---|---|
| Hero boss / mount (fills screen) | raid boss, rideable dragon | 40–60k | nothing visible; instance repeats (scales, teeth) |
| Standard enemy | wolf, zombie hound | 10–20k | mouth bag optional, mitten toes |
| Swarm / ambient | rats, birds, fish | 1–4k | fused limbs, no eye loops, painted detail |
| Static creature prop (corpse, statue) | — | UEFN prop caps apply: complex large ≤ 9k polys, ≤ 5k verts | export as `SM_`, not `SK_` |

Teeth, spines, suckers, scales: instance them (`geometry_nodes`) or bake them (`texture_bake`) — never hand-model hundreds of copies into the skin mesh.

## Adapting joint topology to non-human limbs

The biped joint rule survives everywhere: one loop on the bend crease, ~3 loops on the extensor (outside) side, 2 on the flexor (inside) side; poles hidden in the "armpit" of each limb junction. What changes is where the joints are:

- **Quadruped foreleg**: shoulder blade → elbow (bends backward) → carpus ("wrist", low on the leg) → toes. The scapula slides under the skin: give the scapula region 1–2 extra loops so a helper bone can fake the slide (`rigging_armatures`).
- **Quadruped hindleg**: hip → stifle (knee, bends forward, buried in the flank) → hock (bends backward) → metatarsus → toes.
- **Digitigrade legs** (wolves, raptors, most monsters): the "backwards knee" is the ankle/hock. It folds hard — give it the full 3-outside/2-inside treatment. The metatarsal pillar below it is nearly rigid: 2 rings suffice. Model every joint slightly flexed in rest pose (natural spring stance) so skinning has range both ways.
- **Spine**: one continuous loop band nose → tail; belly and back loops run parallel to it so the ribcage-to-hip mass twists cleanly.
- **Wings**: arm + hand topology with elongated fingers — reuse the knuckle rules from `hands_feet`, then see the membrane section below.

## Tails & tentacles: loop spacing for smooth bends

- Rings perpendicular to the axis, spacing ≈ **0.5–1.0× local diameter**. Wider than that and bends facet; much tighter wastes budget.
- **Constant ring vertex count root → tip.** Taper with radius, never by dropping verts — weights then transfer ring-to-ring and loops stay selectable.
- Cross-section: 8 sides for swarm-tier, 12–16 for standard, 16–24 for hero tentacles that coil on camera.
- Rigging rule of thumb: one bone per 2–3 rings (`rigging_armatures`).

Scriptable build — curve with taper, converted to a ringed tube:

```python
import bpy
cu = bpy.data.curves.new("CU_tentacle", 'CURVE')
cu.dimensions = '3D'
cu.resolution_u = 12          # rings along the length
cu.bevel_depth = 0.10         # base radius, meters
cu.bevel_resolution = 4       # cross-section density
cu.use_fill_caps = True
sp = cu.splines.new('BEZIER')
sp.bezier_points.add(3)
coords = [(0, 0, 0), (0.25, 0.05, 0.45), (0.55, -0.05, 0.85), (0.95, 0.0, 1.05)]
radii = [1.0, 0.7, 0.4, 0.1]  # taper to the tip
for bp, co, r in zip(sp.bezier_points, coords, radii):
    bp.co = co
    bp.handle_left_type = bp.handle_right_type = 'AUTO'
    bp.radius = r
ob = bpy.data.objects.new("SM_tentacle", cu)
bpy.context.collection.objects.link(ob)
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
bpy.ops.object.convert(target='MESH')  # bevel rings become edge loops
```

## Radial mouths & sucker loops

Lamprey mouths, leech maws, octopus suckers — all the same structure: **concentric ring loops around a central axis**, the radial cousin of the orbicularis oris.

- 3+ concentric rings so the sphincter can close; innermost ring is the aperture edge, add one ring folding inward for lip thickness, then continue into a throat tube (the radial "mouth bag").
- Spoke count = ring vertex count; keep it constant across all rings. 16 spokes animates a convincing close; 8 is the swarm floor.
- The poles where radial spokes meet the surrounding surface grid: push them outward into low-deformation skin, exactly like mouth-corner poles in `face_topology`.
- Teeth ring: separate mesh, instanced radially around the aperture — parent or skin to the mouth bones, don't weld into the sphincter loops.
- Suckers are miniature versions: a 2–3 ring shallow inset. Model one, scatter along the tentacle with instancing (`geometry_nodes`); collapse to real geometry only if the sucker must deform.

## Wing membrane topology

- **One mesh.** Membrane shares a welded vertex row with each wing finger and with the body flank — separate objects give skinning seams that tear when the wing folds (`skinning_weights`).
- Primary loops run **parallel to the fingers** (those are the fold lines); secondary loops fan from the body to the trailing edge. Quad grid, no n-gons — the membrane crumples when folding and n-gons crease unpredictably.
- 4–8 quad spans between adjacent fingers: enough to billow and fold, not enough to flap like cloth sim.
- Thickness: model single-sided, then Solidify with a small offset for export; a zero-thickness sheet shades wrong from behind unless the material is two-sided.

```python
obj = bpy.data.objects["SM_wing"]
sol = obj.modifiers.new("Membrane", 'SOLIDIFY')
sol.thickness = 0.015          # 1.5 cm
sol.offset = 0.0               # thicken both ways from the sheet
sol.use_even_offset = True
```

- Trailing-edge scallops between fingers are silhouette — cut them into the mesh, don't fake with alpha unless swarm-tier.

## Generated / sculpted body → hand retopo

Hyper3D (`blender_generate_hyper3d_model_via_text`, import with `blender_import_generated_asset`) and Hunyuan3D (`blender_generate_hunyuan3d_model`, import with `blender_import_generated_asset_hunyuan`) produce tri-soup: great mass reference, never a final skinned mesh. Pipeline:

1. **Merge & even out** — voxel remesh (configure the mesh datablock; the operator takes no parameters):

```python
obj = bpy.data.objects["Body_gen"]
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
me = obj.data
me.remesh_voxel_size = 0.02
me.use_remesh_fix_poles = True
me.use_remesh_preserve_volume = True
bpy.ops.object.voxel_remesh()
```

2. **Flow-less zones** (torso mass, tail, slug bodies) — QuadriFlow gives an even quad grid with no deformation loops; acceptable where nothing folds hard:

```python
bpy.ops.object.quadriflow_remesh(mode='FACES', target_faces=6000,
                                 use_mesh_symmetry=True, seed=1)
```

3. **Loop-critical zones** (head, radial mouth, joints, wing roots) — hand-built template + shrinkwrap, the only scriptable path to correct loops. Build a small template with the ring structure above, then wrap it onto the sculpt:

```python
base = bpy.data.objects["Head_template"]     # clean loops authored by hand
sw = base.modifiers.new("Wrap", 'SHRINKWRAP')
sw.target = bpy.data.objects["Body_gen"]
sw.wrap_method = 'TARGET_PROJECT'
sw.wrap_mode = 'ON_SURFACE'
with bpy.context.temp_override(object=base, active_object=base, selected_objects=[base]):
    bpy.ops.object.modifier_apply(modifier=sw.name)
```

4. **Weld** template zones to the QuadriFlow body: join objects, then in edit mode `bpy.ops.mesh.remove_doubles(threshold=0.001)` on the border verts (there is no `mesh.merge_by_distance` operator — `remove_doubles` IS "Merge by Distance").
5. **Bake** the generated/sculpted detail down onto the retopo (`texture_bake`), then UVs (`uv_workflow`).

Full remesh/decimate trade-offs live in `retopology`; sculpt-detail alternatives in `sculpting`.

## Asymmetry pass — after Mirror apply, never before

Creatures sell realism through asymmetry: one broken horn, a drooping ear, off-center scars. Do all symmetric modeling first, apply the Mirror modifier, save a checkpoint, then nudge regions with proportional editing (the scriptable grab brush):

```python
import bpy, bmesh
from mathutils import Vector
obj = bpy.data.objects["SK_creature"]
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
for m in [m for m in obj.modifiers if m.type == 'MIRROR']:
    bpy.ops.object.modifier_apply(modifier=m.name)
bpy.ops.wm.save_mainfile()                    # checkpoint before breaking symmetry
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(obj.data)
target = Vector((0.35, 0.10, 1.60))           # e.g. left horn base, world space
for v in bm.verts:
    v.select = (obj.matrix_world @ v.co - target).length < 0.15
bmesh.update_edit_mesh(obj.data)
bpy.ops.transform.translate(value=(0.03, 0.0, 0.05),
    use_proportional_edit=True, proportional_edit_falloff='SMOOTH',
    proportional_size=0.3)
bpy.ops.object.mode_set(mode='OBJECT')
```

Repeat with `bpy.ops.transform.resize` / `rotate` (same proportional args) for shrunken or twisted features. Keep asymmetry off the loop structure itself — move verts, don't re-cut topology, or mirrored UV/weight workflows break. Alternative: store the asymmetry as a shape key so it stays dialable (`shape_keys`).

## Verify

- `blender_get_viewport_screenshot` from front, side, top and one 3/4 view — the silhouette must read as the creature at thumbnail size; if it only reads with shading, the silhouette budget is misallocated.
- Wireframe screenshot on each folding joint (hock, elbow, wing fingers): loop on the crease, denser outside than inside, no pole sitting on a bend line.
- Tail/tentacle: ring spacing even in side view, same vertex count per ring (`blender_get_object_info` vertex count sanity check after edits).
- Radial mouth: select an inner ring loop mentally in the wireframe — every ring must be a closed loop, no spiral drift.
- After the asymmetry pass: overlay front screenshot vs. the pre-pass checkpoint — changes should be feature-level (horn, ear), not a global lean.

## Don'ts

- Don't ship Hyper3D/Hunyuan tri-soup as the skinned mesh — retopo first, always.
- Don't QuadriFlow a face, radial mouth, or folding joint and expect animation loops; it has no edge-flow awareness.
- Don't sculpt asymmetry before the Mirror modifier is applied — it either gets mirrored away or blocks the modifier workflow.
- Don't vary cross-section vertex count along a tail or tentacle to "save polys" — taper radius instead.
- Don't build wing membranes as separate objects from the arm; weld into one mesh before skinning.
- Don't hand-place hundreds of suckers/teeth/spines — instance or bake.
- Don't call `bpy.ops.mesh.merge_by_distance` — it doesn't exist; use `bpy.ops.mesh.remove_doubles`.
- Don't model every joint dead-straight in rest pose; slight flexion gives skinning room in both directions.

See also: `body_anatomy`, `face_topology`, `retopology`, `sculpting`, `skinning_weights`, `rigging_armatures`, `lod_collision`, `skeletal_export`.
