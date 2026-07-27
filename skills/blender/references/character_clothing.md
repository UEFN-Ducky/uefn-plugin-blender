# Character clothing

Game clothing for rigged characters: build garments as shells duplicated from the body, add real thickness, fold detail, and transfer the body's skin weights. Load this when dressing a character that already has a body mesh (see `body_anatomy`) — not for standalone cloth simulation (see `cloth`).

## Garment strategy

| Garment type | Method | Why |
|---|---|---|
| Tight (shirt, pants, gloves, boots) | Duplicate body faces → separate → Solidify | Inherits body topology, so it deforms in lockstep and weight transfer is near-perfect |
| Loose (coat, skirt, cape, hood) | Blockout separately, optional cloth-sim assist for drape/folds, then cleanup | Body topology doesn't match a hanging silhouette |
| Rigid (belts, pouches, armor plates, buckles) | Separate hard-surface meshes, weighted 100% to one bone | No deformation needed; cheap and clip-proof |

Always `bpy.ops.wm.save_mainfile()` before the destructive steps (separate, apply, delete).

## Shell workflow: duplicate → separate → solidify

Mark the garment region on the body as a vertex group first (in Edit Mode select the faces, `bpy.ops.object.vertex_group_assign_new()`, rename it). Then:

```python
import bpy
body = bpy.data.objects["Body"]
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
bpy.context.view_layer.objects.active = body

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='DESELECT')
body.vertex_groups.active = body.vertex_groups["ShirtRegion"]
bpy.ops.object.vertex_group_select()
before = set(bpy.data.objects)
bpy.ops.mesh.duplicate()                    # copy the region, keep the body intact
bpy.ops.mesh.separate(type='SELECTED')      # duplicated faces -> new object
bpy.ops.object.mode_set(mode='OBJECT')
shirt = (set(bpy.data.objects) - before).pop()
shirt.name = "Shirt"
```

Push the shell off the skin, then thicken. Keeping both as live modifiers lets you retune fit after posing tests:

```python
fit = shirt.modifiers.new("Fit", 'SHRINKWRAP')
fit.target = body
fit.wrap_method = 'NEAREST_SURFACEPOINT'
fit.wrap_mode = 'ABOVE_SURFACE'             # hold every vert at a fixed clearance
fit.offset = 0.004                          # 4 mm skin gap (scene in meters)

sol = shirt.modifiers.new("Solidify", 'SOLIDIFY')
sol.thickness = 0.0025
sol.offset = 1.0                            # grow outward; inner surface stays at the fit gap
sol.use_even_offset = True
sol.use_rim = True                          # closes neck/sleeve/hem borders with quads
```

### Clearance and thickness values (scene in meters, 1 unit = 1 m)

| Garment | Skin clearance (Shrinkwrap offset) | Solidify thickness |
|---|---|---|
| T-shirt / jersey | 0.003–0.005 | 0.002–0.003 |
| Hoodie / sweater | 0.005–0.008 | 0.004–0.006 |
| Jacket / coat | 0.008–0.012 | 0.006–0.010 |
| Leather / padded armor | 0.010–0.015 | 0.010–0.020 |

Too-thin rims disappear at gameplay camera distance (UEFN character ≈ 1.9 m tall); err thicker than real-world for readability.

## Openings, collars, cuffs, hems

Cut openings (neck, wrist, waist) by deleting face rings before Solidify — `use_rim=True` closes each border cleanly. Save the border loop as a vertex group when you cut it; you'll reuse it for collars and pinning.

Collar/cuff: extrude the border loop up and flare it. Scaling uses the selection median, which sits on the loop's center axis, so an XY resize flares it outward:

```python
shirt.vertex_groups.active = shirt.vertex_groups["NeckEdge"]
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.object.vertex_group_select()
bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": (0, 0, 0.015)})
bpy.ops.transform.resize(value=(1.06, 1.06, 1.0))
bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": (0, 0, 0.015)})
bpy.ops.object.mode_set(mode='OBJECT')
```

Hem: add one horizontal loop just above the garment bottom so the border holds its shape and weights grade cleanly. `loopcut_slide` needs an interactive 3D-view context — use a bisect instead, which is fully scriptable:

```python
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.bisect(plane_co=(0, 0, 1.02), plane_no=(0, 0, 1))   # loop at z = 1.02 m
bpy.ops.object.mode_set(mode='OBJECT')
```

Cuffs and collars carry most of the garment's silhouette read — give them a full extra loop and slightly exaggerated radius rather than relying on texture.

## Folds

Split the work: **silhouette folds are modeled, micro-wrinkles live in the normal map** (bake from a detail pass — see `texture_bake`).

Manual folds (default, fully controllable): add loops across compression zones — inner elbow, armpit, waistband, back of knee — then offset alternate loops in/out a few mm. The scriptable grab brush is proportional editing on a selected vert cluster:

```python
bpy.ops.transform.translate(value=(0, 0.006, 0), use_proportional_edit=True,
    proportional_edit_falloff='SMOOTH', proportional_size=0.06)
```

Cloth-sim assist (optional, for loose garments): let the solver find the drape, freeze one frame, then clean up. The body needs a Collision modifier; pin the garment where it's held (collar, shoulder seam, waistband) via a "Pin" vertex group:

```python
body.modifiers.new("BodyCol", 'COLLISION')
mod = shirt.modifiers.new("Cloth", 'CLOTH')
mod.settings.quality = 7
mod.settings.mass = 0.3
mod.settings.vertex_group_mass = "Pin"            # this IS the pin group property
mod.collision_settings.use_self_collision = True
mod.collision_settings.distance_min = 0.003
mod.point_cache.frame_start, mod.point_cache.frame_end = 1, 60
with bpy.context.temp_override(point_cache=mod.point_cache):  # ctx dict removed in 4.0
    bpy.ops.ptcache.bake(bake=True)
bpy.context.scene.frame_set(45)                   # pick the best-looking frame
bpy.ops.object.modifier_apply(modifier=mod.name)  # object mode, object active
```

Cleanup after applying the sim — it is a shaping pass, never final topology:

```python
import bmesh
bm = bmesh.new(); bm.from_mesh(shirt.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0008)
bm.to_mesh(shirt.data); bm.free()

cs = shirt.modifiers.new("Relax", 'CORRECTIVE_SMOOTH')
cs.factor = 0.5
cs.iterations = 5
bpy.ops.object.modifier_apply(modifier=cs.name)
```

Full solver parameters and pressure/sewing options: `cloth`.

## Delete hidden body faces

Any body face fully covered by opaque clothing is wasted verts and a guaranteed clip risk in animation. Delete it — don't just hide it. Keep 1–2 face rows of body past every garment border as a safety overlap. If you built the shell from a vertex group, that same group (minus the border rows) selects the faces to remove:

```python
bpy.context.view_layer.objects.active = body
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='DESELECT')
body.vertex_groups.active = body.vertex_groups["TorsoHidden"]
bpy.ops.object.vertex_group_select()
bpy.ops.mesh.select_less()                 # keep a safety border row
bpy.ops.mesh.delete(type='FACE')
bpy.ops.object.mode_set(mode='OBJECT')
```

Only keep the full body if the character genuinely swaps outfits at runtime.

## Deformation-friendly topology

- Clothing loop rings across joints must **match the body's ring counts and positions** (elbow/knee/shoulder patterns per `body_anatomy`): matched topology + matched weights = no divergence when posed.
- Quads only across deforming zones; horizontal rings around limbs and torso.
- Flat panels (chest, back, skirt panels) can run sparser than the body — but never reduce density across a bend zone.
- Put a full loop exactly at every garment border (collar, cuff, hem) so transferred weights grade cleanly instead of stair-stepping.

## Weight transfer from the body

Never paint garment weights from scratch — transfer, then touch up. Do this while the shell is still single-layer if possible; a live Solidify propagates vertex groups to the generated inner/rim verts.

```python
bpy.context.view_layer.objects.active = shirt
dt = shirt.modifiers.new("Weights", 'DATA_TRANSFER')
dt.object = body
dt.use_vert_data = True
dt.data_types_verts = {'VGROUP_WEIGHTS'}
dt.vert_mapping = 'POLYINTERP_NEAREST'
dt.layers_vgroup_select_src = 'ALL'
bpy.ops.object.datalayout_transfer(modifier=dt.name)   # create matching group names first
bpy.ops.object.modifier_apply(modifier=dt.name)

arm = shirt.modifiers.new("Armature", 'ARMATURE')
arm.object = bpy.data.objects["Rig"]
shirt.parent = bpy.data.objects["Rig"]
```

Normalization, per-vertex influence limits, and smoothing passes: `skinning_weights`.

## Intersections at animation extremes

Test before export, not after import. Pose the rig at the extremes and screenshot each risk zone:

```python
rig = bpy.data.objects["Rig"]
pb = rig.pose.bones["upperarm_l"]
pb.rotation_mode = 'XYZ'
pb.rotation_euler = (0.0, 0.0, 1.4)        # ~80 deg arm raise
bpy.context.view_layer.update()
```

Test set: arms fully raised, elbows fully bent, deep crouch, maximum spine twist. Fix in this order:

1. Identical weights (transfer above) — matched weights cannot diverge.
2. More clearance where weights legitimately differ (loose hems, coat skirts).
3. Delete more body underneath the problem area.
4. Corrective shape key driven by the bone as a last resort (`shape_keys`).

## Budgets

- Skinned meshes get no Nanite benefit in UEFN — every clothing tri renders at full cost. Stylized UEFN character including outfit: roughly 15–40k tris; the outfit is typically half or more of that since it *is* the visible silhouette. Epic's own cinematic ceiling: MetaHuman body ≈ 30,500 verts at LOD0.
- Rigid attachments (belt, pouch, buckle): a few hundred tris each, 100% weighted to one bone.
- One material section per garment maximum; ideally one shared texture set for the whole outfit (`uv_workflow`).
- Export with the body as one skeletal mesh via `skeletal_export`; apply Solidify and all fold modifiers before export (Armature stays live).

## Version notes

- All modifiers used here (`SOLIDIFY`, `SHRINKWRAP`, `CLOTH`, `DATA_TRANSFER`, `CORRECTIVE_SMOOTH`, `ARMATURE`) keep the same names and properties across 4.2 LTS → 5.0.
- `bpy.ops.ptcache.bake` requires `bpy.context.temp_override(point_cache=...)`; the old context-dict argument was removed in 4.0.
- 5.0 only: if you cut straps/holes with booleans, the fast solver enum renamed `'FAST'` → `'FLOAT'` (`'EXACT'` unchanged).

## Verify

- Rest pose: `blender_get_viewport_screenshot` front/side/back — no z-fighting at borders, rims visible at distance.
- Each extreme pose: screenshot elbow, armpit, shoulder, hip, knee — zero body poke-through.
- `blender_get_object_info` on each garment: tri count vs budget, no loose verts after sim cleanup.
- Solidify rims: borders closed (no non-manifold edges except intended openings).

## Don'ts

- Don't Solidify a shell sitting exactly on the skin — the inner surface z-fights the body; always offset first.
- Don't ship cloth-sim output raw — merge doubles and relax, or it will shade and deform badly.
- Don't leave the full body under opaque clothing "just in case".
- Don't hand-paint garment weights before trying a transfer.
- Don't reduce garment loop density across a joint the body still bends.
- Don't give every garment its own material — UEFN wants minimal material sections.

See also: `body_anatomy`, `skinning_weights`, `cloth`, `shape_keys`, `uv_workflow`, `texture_bake`, `skeletal_export`, `verify_loop`.
