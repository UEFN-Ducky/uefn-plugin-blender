# Vehicles & Mechs

Cars, trucks, tanks, aircraft, mechs, turrets — hard-surface shells with articulated parts (wheels, doors, turrets) that UEFN animates by rotating separate static meshes around their own pivots.

## Build order

1. Blueprint refs in (below), then blockout the shell with a Mirror modifier (`blockout`).
2. **Split movable parts into separate objects before surfacing** — cutting a door out of a beveled, creased shell later is misery.
3. Surface the body: sub-d + creases OR mid-poly (decision table below).
4. Wheels via radial array. Greebles (handles, lights, antennas, mirrors) last, after big forms are locked.
5. Pivots, naming, hierarchy; then UVs (`uv_workflow`), bakes (`texture_bake`), LODs + UCX (`lod_collision`), export (`uefn_export`).
6. `bpy.ops.wm.save_mainfile()` before every destructive apply (mirror, boolean, decimate).

A walking mech is a skeletal asset: rig it (`rigging_armatures`) and export via `skeletal_export`. Wheeled/tracked/turreted machines are static parts — this file.

## Blueprint reference setup

Work in meters, real size (1 BU = 1 m; sedan ≈ 4.5 m long × 1.45 m tall, UEFN character capsule 1.92 m). Load side/front/top blueprints as image empties, ortho-only so perspective views stay clean:

```python
import bpy, math

def add_ref(name, path, rot_deg, loc):
    img = bpy.data.images.load(path)
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = 'IMAGE'
    e.data = img
    e.empty_display_size = 5.0            # longest image dimension in meters — match vehicle length
    e.empty_image_side = 'FRONT'
    e.show_empty_image_perspective = False
    e.use_empty_image_alpha = True
    e.color[3] = 0.4                      # fade so your mesh reads on top
    e.rotation_euler = [math.radians(a) for a in rot_deg]
    e.location = loc
    bpy.context.scene.collection.objects.link(e)
    return e

add_ref("REF_side",  r"C:/refs/side.png",  (90, 0, 90), (-2.0, 0, 1.0))  # view from +X
add_ref("REF_front", r"C:/refs/front.png", (90, 0, 0),  (0, 3.0, 1.0))   # view from -Y
add_ref("REF_top",   r"C:/refs/top.png",   (0, 0, 0),   (0, 0, -0.05))   # view from +Z
```

Push each ref past the far side of the body so it never z-fights the mesh. Match silhouettes in ortho views with the screenshot loop (`verify_loop`); full ref-matching technique lives in `reference_match`.

## Body surfacing: sub-d + creases vs mid-poly

| Shell | Choose | Why |
|---|---|---|
| Flowing curvature: sports car, fuselage, canopy | Sub-D + edge creases, apply at level 1–2 | Continuous highlights; bake down for game |
| Paneled/faceted: military, truck, mech plating | Mid-poly: Bevel + Weighted Normal | No bake needed, cheap, reads perfectly at gameplay distance |
| Background filler vehicle | Low-poly + Smooth by Angle only | Budget |

Mid-poly + weighted normals is the dominant vehicle norm: real 3–8 mm bevels instead of support loops, normals bent onto the big flat faces so the shading transition lives only on the bevel.

### Sub-D + creases

Edge crease is the `crease_edge` float edge attribute (the old `MeshEdge.crease` is gone):

```python
import bpy
obj = bpy.data.objects["SM_Jeep_Body"]
me = obj.data
cr = me.attributes.get("crease_edge") or me.attributes.new("crease_edge", 'FLOAT', 'EDGE')
for e in me.edges:
    if e.select:                          # select panel-break edges in edit mode first
        cr.data[e.index].value = 0.85     # 1.0 = knife-sharp; 0.6-0.9 = soft body-panel break
sub = obj.modifiers.new("Subdiv", 'SUBSURF')
sub.levels = sub.render_levels = 2
```

Keep the cage light (a car hood is ~6×4 quads before subdivision). Apply at level 1–2 for the game mesh, never export a live level-3 subsurf.

### Mid-poly: Bevel + Weighted Normal + hard edges

```python
import bpy, math
obj = bpy.data.objects["SM_Tank_Hull"]
with bpy.context.temp_override(object=obj, active_object=obj,
                               selected_objects=[obj], selected_editable_objects=[obj]):
    # Writes smooth shading + the sharp_edge attribute directly (no modifier).
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(30), keep_sharp_edges=True)
bev = obj.modifiers.new("Bevel", 'BEVEL')
bev.width = 0.006                          # 6 mm — real-world panel-edge radius
bev.segments = 2
bev.limit_method = 'ANGLE'
bev.angle_limit = math.radians(40)
wn = obj.modifiers.new("WN", 'WEIGHTED_NORMAL')
wn.mode = 'FACE_AREA'
wn.keep_sharp = True
wn.weight = 50
```

`bpy.ops.object.shade_auto_smooth(angle=...)` is the modifier-based alternative (adds the "Smooth by Angle" node-group modifier) — fine for viewport work, but bake sharpness in with `shade_smooth_by_angle` before export so no modifier ordering surprises.

### Panel lines

On mid-poly shells, cut with a boolean:

```python
import bpy
body = bpy.data.objects["SM_Tank_Hull"]
cut = bpy.data.objects["panel_cutter"]     # thin box lattice tracing the panel gaps
b = body.modifiers.new("Panels", 'BOOLEAN')
b.operation = 'DIFFERENCE'; b.object = cut; b.solver = 'EXACT'
cut.display_type = 'WIRE'; cut.hide_render = True
```

On sub-d shells do NOT boolean — creased insets instead (inset the panel face, crease the inset loop); booleans under subdivision pinch. Clean boolean debris (`mesh_cleanup`) before shading verification.

## Wheels: radial construction via Array

Base rim/tire is a cylinder with the axle along local X (vehicle faces -Y):

```python
import bpy, math
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.36, depth=0.24,
                                    rotation=(0, math.radians(90), 0),
                                    location=(0.85, 1.45, 0.36))
bpy.context.active_object.name = "SM_Jeep_Wheel_FL"
```

24 sides is right for a medium-vehicle LOD0; 12–16 for small/background. Spokes, bolts, and tread blocks: model ONE at 12 o'clock, then radial-array around a rotated empty. The spoke's origin must sit at hub center and the empty at the same point — the object-offset delta is then pure rotation:

```python
import bpy, math
spoke = bpy.data.objects["spoke"]          # origin already at hub center
piv = bpy.data.objects.new("HLP_wheel_pivot", None)
bpy.context.collection.objects.link(piv)
piv.location = spoke.location
piv.rotation_euler.x = math.radians(360 / 8)   # axle along X; 8 copies
arr = spoke.modifiers.new("Radial", 'ARRAY')
arr.use_relative_offset = False
arr.use_object_offset = True
arr.offset_object = piv
arr.count = 8
```

Apply the array, join spoke set into the wheel, then duplicate for the other corners: **duplicate + rotate 180° around Z** for the far side — never mirror with scale -1 (flipped normals, broken pivots in UEFN).

## Movable parts: origins and pivots

UEFN rotates each part around its own mesh origin. Set origins deliberately:

| Part | Origin at | Rotation axis |
|---|---|---|
| Wheel | Hub center | Local X (axle) |
| Door | On the hinge line (bottom hinge) | Local Z (vertical) |
| Turret | Center of turret ring, on the ring plane | Local Z (yaw) |
| Barrel / gun | Trunnion (pitch pivot), not the muzzle | Local X (pitch) |
| Hatch / ramp | Hinge edge midpoint | Along the hinge edge |

```python
import bpy

def set_origin(obj, world_pos):
    bpy.context.scene.cursor.location = world_pos
    with bpy.context.temp_override(object=obj, active_object=obj,
                                   selected_objects=[obj], selected_editable_objects=[obj]):
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

set_origin(bpy.data.objects["SM_Jeep_Wheel_FL"], (0.85, 1.45, 0.36))  # hub, from blender_get_object_info
set_origin(bpy.data.objects["SM_Jeep_Door_L"],   (0.80, 0.55, 0.45))  # bottom of hinge line
```

Before setting pivots, apply rotation and scale on every part (`bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)`) so local axes are world-aligned and clean in UEFN. Keep location unapplied — parts stay assembled.

## Interior decision

| Camera use in UEFN | Interior |
|---|---|
| Enterable, first-/close third-person driving | Simple cockpit shell: seat, dash, wheel/sticks — budget 15–25% of the vehicle |
| Turret gunner view | Model only what that camera sees |
| Set dressing / drive-by only | None — opaque or heavily tinted glass over a black inner shell |

Decide before UVing; an interior added late fragments the UV layout and doubles material sections.

## Part naming & hierarchy

`SM_<Vehicle>_<Part>` per `scene_organization`: `SM_Jeep_Body`, `SM_Jeep_Wheel_FL/FR/RL/RR`, `SM_Jeep_Door_L/R`, `SM_Tank_Turret`, `SM_Tank_Barrel`. Collision: `UCX_SM_Jeep_Body_01`. Everything in a `COL_Jeep` collection. Parent movables to the body, preserving world transforms:

```python
import bpy
body = bpy.data.objects["SM_Jeep_Body"]
for name in ("SM_Jeep_Wheel_FL", "SM_Jeep_Wheel_FR", "SM_Jeep_Wheel_RL",
             "SM_Jeep_Wheel_RR", "SM_Jeep_Door_L", "SM_Jeep_Door_R"):
    o = bpy.data.objects[name]
    o.parent = body
    o.matrix_parent_inverse = body.matrix_world.inverted()
```

## Budgets (UEFN vehicle targets, Epic best-practices)

| Vehicle size | LOD0 verts | LOD3 verts |
|---|---|---|
| Small (bike, cart) | 1,200 | 200 |
| Medium (car, jeep) | 6,000 | 400 |
| Large (tank, aircraft) | 9,000 | 1,000 |

Ship 3 LODs minimum; kill antennas, mirrors, rails, and bolt detail by LOD1. Textures ≤ 2K power-of-2; aim for one material section per part; ≤ 10 UCX primitives per mesh (`lod_collision`). Spend the budget where the camera lives: 60%+ on the body shell, wheels ~10% each corner at most.

## Version notes

- Boolean solver: `'EXACT'` is unchanged across the window; 5.0 renames `'FAST'` → `'FLOAT'` — guard any fast-solver code.
- Sharpness/smoothing across 4.2→5.0 is `shade_smooth_by_angle` / `shade_auto_smooth` + the `sharp_edge` edge attribute. `mesh.use_auto_smooth` no longer exists — never write it.
- Edge crease is the `crease_edge` attribute in the whole window.

## Verify

- Ortho side/front `blender_get_viewport_screenshot` over the ref empties — silhouette must land on the blueprint lines.
- `blender_get_object_info` on each movable part: origin at hub/hinge/ring, rotation `(0,0,0)`, scale `(1,1,1)`.
- Pivot spin test: `bpy.data.objects["SM_Jeep_Wheel_FL"].rotation_euler.x += math.radians(30)` → screenshot → wheel turns about its axle without orbiting → undo the rotation.
- Shading screenshot at 3/4 view: flat panels shade flat, transitions only on bevels — no gradient smears (weighted normals working), no black triangles (flipped normals).
- Poly counts per part vs the budget table via `blender_get_object_info`.

## Don'ts

- Don't mirror wheels/doors with scale -1 — duplicate and rotate 180° instead.
- Don't leave part origins at world center; UEFN animates around the origin you export.
- Don't join movable parts into the body mesh "to tidy up" — separation IS the feature.
- Don't boolean panel lines into a live-subsurf shell; use creased insets there.
- Don't model interiors for vehicles never entered on camera.
- Don't greeble before the blockout matches the blueprints — detail hides proportion errors.

See also: `hard_surface`, `blockout`, `reference_match`, `mesh_cleanup`, `lod_collision`, `uefn_export`, `scene_organization`.
