# Blockout

Proportion-first massing pass: nail real-world scale and silhouette with primitives before any detail work. Load this before modeling anything bigger than a handheld prop, and always for buildings, vehicles, and characters.

## What a blockout must answer

| Question | Pass criterion |
|---|---|
| Scale | Every mass has real-world dimensions in meters (1 BU = 1 m, scale 1.0) |
| Proportion | Ratios read correctly next to a 1.9 m character reference |
| Silhouette | Object is identifiable from a flat grey screenshot at gameplay distance |
| Gameplay fit | Doors ≥ 2.1 m, character clearance everywhere a player walks |
| Grid fit (buildings) | Footprint aligns to the 512 uu = 5.12 m Fortnite tile; wall height 3.84 m |

Work in meters at real size. UEFN conversion (1 uu = 1 cm) is handled at export — see `uefn_export`.

## Scale reference rig — build it first

Drop these into every blockout scene. Nothing else tells you if 4 m is "big".

```python
import bpy

def ensure_coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c

def move_to(ob, coll):
    for c in ob.users_collection:
        c.objects.unlink(ob)
    coll.objects.link(ob)

ref = ensure_coll("COL_REF")
# Fortnite character proxy: 1.9 m tall capsule stand-in
bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=1.9, location=(0.0, -4.0, 0.95))
man = bpy.context.active_object; man.name = "REF_Character_190cm"; move_to(man, ref)
# Door slab: 2.1 m tall x 1.0 m wide
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(1.5, -4.0, 1.05))
door = bpy.context.active_object; door.name = "REF_Door_210cm"
door.dimensions = (1.0, 0.1, 2.1); move_to(door, ref)
# Building tile footprint: 512 uu = 5.12 m
bpy.ops.mesh.primitive_plane_add(size=5.12, location=(0.0, 0.0, 0.0))
tile = bpy.context.active_object; tile.name = "REF_Tile_512uu"; move_to(tile, ref)
```

## Massing with primitives

Cubes and cylinders only. Set `obj.dimensions` in meters, bake scale to 1.0 immediately — live scale poisons booleans, bevels, and export later.

```python
def block(name, dims, loc, coll_name="COL_Blockout_A"):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.active_object
    ob.name = name                      # SM_Block_* until final merge
    ob.dimensions = dims                # world-space meters
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    move_to(ob, ensure_coll(coll_name))
    return ob

body  = block("SM_Block_Body",  (4.0, 6.0, 3.0), (0.0, 0.0, 1.5))
tower = block("SM_Block_Tower", (2.0, 2.0, 7.0), (2.5, -1.5, 3.5))
```

Rules of the massing pass:

- 5–20 masses per option. If you have 50, you started detailing.
- Sit everything on Z=0 ground plane; heights become readable numbers (`top at 3.00 m`).
- Buildings: footprints in multiples of 5.12 m, floor-to-floor 3.84 m (matches Fortnite 512×384 wall tile) so the asset snaps in-world.
- No bevels, no subdivision, no materials. Shape and size only.

## Booleans: rough openings only, keep them live

Cut door/window holes so silhouette and playability read, but keep modifiers unapplied until approval — approved blockouts get rebuilt clean in the detail pass anyway.

```python
def cut(target, cutter):
    m = target.modifiers.new("Bool", 'BOOLEAN')
    m.operation = 'DIFFERENCE'
    m.object = cutter
    m.solver = 'EXACT'   # 5.0: fast solver enum renamed 'FAST' -> 'FLOAT'; 'EXACT' is unchanged
    cutter.display_type = 'WIRE'
    cutter.hide_render = True
    return m

hole = block("SM_Block_DoorCut", (1.0, 0.6, 2.1), (0.0, -3.0, 1.05), "COL_Blockout_A")
cut(body, hole)
```

Save a checkpoint (`bpy.ops.wm.save_mainfile()`) before applying any boolean. To apply after approval:

```python
with bpy.context.temp_override(object=body, active_object=body, selected_objects=[body]):
    bpy.ops.object.modifier_apply(modifier="Bool")
```

## Block multiple options fast

Silhouette decisions are cheap now and expensive later. Duplicate the whole option collection, offset it, vary the masses, and compare all options in one screenshot.

```python
def dup_option(src_name, dst_name, dx=12.0):
    src = bpy.data.collections[src_name]
    dst = ensure_coll(dst_name)
    for ob in list(src.objects):
        cp = ob.copy()
        cp.data = ob.data.copy()        # independent mesh so edits don't leak between options
        cp.location.x += dx
        dst.objects.link(cp)
    return dst

dup_option("COL_Blockout_A", "COL_Blockout_B", 12.0)
dup_option("COL_Blockout_A", "COL_Blockout_C", 24.0)
# now reshape B and C: taller tower, wider body, different roof mass, etc.
```

Two or three options minimum for anything hero-sized. Delete losing collections outright; don't hoard.

## Grey matcap + eye-height silhouette screenshots

Judge blockouts in flat grey — color and lighting hide proportion errors. Then screenshot from character eye height (~1.75 m for a 1.9 m character), because that is where players actually see the asset.

```python
from mathutils import Vector

def grey_matcap():
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            sh = area.spaces.active.shading
            sh.type = 'SOLID'
            sh.light = 'MATCAP'                 # default matcap is a neutral grey
            sh.color_type = 'SINGLE'
            sh.single_color = (0.6, 0.6, 0.6)

def eye_view(eye=(8.0, -8.0, 1.75), target=(0.0, 0.0, 1.5)):
    eye, target = Vector(eye), Vector(target)
    d = target - eye
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            sp = area.spaces.active
            sp.lens = 50.0                      # wide lenses lie about proportion
            r3d = sp.region_3d
            r3d.view_perspective = 'PERSP'
            r3d.view_rotation = d.normalized().to_track_quat('-Z', 'Y')
            r3d.view_location = target
            r3d.view_distance = d.length

grey_matcap()
eye_view()
```

Then `blender_get_viewport_screenshot`. Shoot at least: eye-height 3/4 front, eye-height side, and a top-down for footprint/grid checks. Full loop discipline lives in `verify_loop`.

## Measure with code, not eyeballs

Screenshots judge silhouette; numbers judge scale. Verify both every iteration.

```python
from mathutils import Vector

def world_dims(ob):
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    lo = Vector((min(p[i] for p in pts) for i in range(3)))
    hi = Vector((max(p[i] for p in pts) for i in range(3)))
    return (hi - lo), lo, hi

for ob in bpy.data.collections["COL_Blockout_A"].objects:
    d, lo, hi = world_dims(ob)
    print(f"{ob.name}: {d.x:.2f} x {d.y:.2f} x {d.z:.2f} m  (top at {hi.z:.2f} m)")

SPEC = {"SM_Block_Body": (4.0, 6.0, 3.0), "SM_Block_Tower": (2.0, 2.0, 7.0)}
for name, want in SPEC.items():
    d, _, _ = world_dims(bpy.data.objects[name])
    for axis, w, got in zip("XYZ", want, d):
        if abs(w - got) > 0.05:
            print(f"FIX {name} {axis}: {got:.2f} m vs spec {w:.2f} m")
```

`blender_get_object_info` also reports per-object transforms/dimensions if you want the tool-side view.

## The approval gate

A blockout is approved when ALL of these hold — only then do detail passes start:

1. Silhouette identifiable in flat grey at eye height and at gameplay distance (zoomed-out shot).
2. Every mass matches its spec dimension within 5 cm (measured with code, printed, checked).
3. Character/door refs read correctly standing next to the asset in a screenshot.
4. Buildings align to the 5.12 m tile and 3.84 m floor height; doors ≥ 2.1 m.
5. One option chosen; losing options deleted; scale applied (1.0) on every object.
6. File saved as a checkpoint (`bpy.ops.wm.save_mainfile()`).

After approval, hand off: `hard_surface` or `props` for mechanical detail, `organic_forms` for creatures/characters, `environments_modular` for kit pieces. The blockout masses become the proportion cage — detail geometry replaces them, it does not reinterpret them.

## Version notes

- Boolean solver enum: `'FAST'` renamed to `'FLOAT'` in 5.0; `'EXACT'` works across 4.2–5.0. Prefer `'EXACT'` in shared scripts.
- Everything else in this file runs unchanged on 4.2 LTS through 5.0.

## Verify

- `blender_get_viewport_screenshot` after `grey_matcap()` + `eye_view()`: silhouette reads, no lighting/color distraction, character ref visible for scale.
- Run the `world_dims` report: every mass within 5 cm of spec, top heights sensible, nothing below Z=0.
- `blender_get_scene_info`: only `COL_REF` + one `COL_Blockout_*` collection remain at approval; all objects `SM_Block_*` named.
- Top-down screenshot over `REF_Tile_512uu`: building footprints land on the tile grid.

## Don'ts

- Don't detail before the gate: no bevels, subdivision, materials, or sculpting on blockout masses.
- Don't eyeball scale — a 2.4 m door "looks fine" alone and reads cartoonish next to the 1.9 m character.
- Don't leave non-1.0 scale on any mass; bake with `transform_apply` right after setting `dimensions`.
- Don't judge proportion through a wide viewport lens or an orbiting bird's-eye view; use 50 mm at 1.75 m eye height.
- Don't iterate on one option in place for an hour; duplicate the collection and diverge, then compare side by side.
- Don't apply blockout booleans early — keep them live so masses stay re-sizeable.

See also: `verify_loop`, `scene_organization`, `reference_match`, `hard_surface`, `organic_forms`, `props`, `environments_modular`, `uefn_export`.
