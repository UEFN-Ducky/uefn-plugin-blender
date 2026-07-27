# bpy fundamentals

The survival kit for every `blender_execute_blender_code` call: the bpy.data / bpy.context / bpy.ops mental model, selection-active-mode discipline, context overrides, the bmesh pattern, transforms, collections, checkpoints, and the exceptions that kill scripts. Load this before writing any nontrivial bpy.

## The three namespaces

| Namespace | What it is | When to use |
|---|---|---|
| `bpy.data` | Every datablock in the file (objects, meshes, materials, collections…) | Default. Direct, deterministic, no context needed. |
| `bpy.context` | What is "current": scene, view layer, active object, selection, mode | Read state; feed ops; set active/selection before ops. |
| `bpy.ops` | Operators (the UI's buttons) | Only when no data-level API exists (mode switches, transform_apply, modifier_apply, remesh, export). Ops depend on context and can fail `poll()`. |

Rule: **prefer `bpy.data` assignment over `bpy.ops`**. `ob.location.z = 1.0` beats `bpy.ops.transform.translate(...)` — no selection, no mode, no poll to get wrong.

## Getting objects by name

```python
import bpy
ob = bpy.data.objects.get("SM_Crate")      # None if missing — never index blind
if ob is None:
    raise RuntimeError("SM_Crate not found: " + str(sorted(o.name for o in bpy.data.objects)))
mesh = ob.data                              # the Mesh datablock (may be shared by other objects)
```

- Names are unique per datablock type; a clash gets a `.001` suffix. If a lookup fails, list names (as above) — your object is probably `SM_Crate.001`.
- Object name and mesh name are independent. Keep them equal: `ob.data.name = ob.name`.
- `bpy.data.objects` is the whole file; `bpy.context.scene.objects` is only what's in the current scene.

## Selection / active / mode discipline

Ops read three things: **selection** (`ob.select_set(True)`), **active object** (`bpy.context.view_layer.objects.active`), and **mode**. Set all three explicitly — never assume prior state:

```python
import bpy
if bpy.context.mode != 'OBJECT':                 # context.mode reads 'EDIT_MESH', 'OBJECT', ...
    bpy.ops.object.mode_set(mode='OBJECT')       # mode_set takes 'EDIT', 'OBJECT', 'SCULPT', ...
for o in bpy.context.selected_objects:           # deselect via data, not ops
    o.select_set(False)
ob = bpy.data.objects["SM_Crate"]
ob.select_set(True)
bpy.context.view_layer.objects.active = ob       # active and selected are independent!
```

Gotchas: `bpy.context.mode` and `mode_set(mode=...)` use *different* enum spellings (`'EDIT_MESH'` vs `'EDIT'`). An object can be active but not selected, or selected but not active — many ops need both. Hidden objects can't be selected; `ob.hide_set(False)` first. End every script back in `'OBJECT'` mode.

## temp_override for context-dependent ops

The old context-dict argument (`bpy.ops.x.y({"object": ob}, ...)`) was removed in 4.0. The only pattern is:

```python
import bpy
ob = bpy.data.objects["SM_Crate"]
with bpy.context.temp_override(object=ob, active_object=ob,
                               selected_objects=[ob], selected_editable_objects=[ob]):
    bpy.ops.object.modifier_apply(modifier=ob.modifiers[0].name)
```

Keys mirror `bpy.context` member names. For viewport-dependent ops add `window=`, `area=`, `region=` (find an area via `bpy.context.window.screen.areas`). Note `modifier_apply` also fails on multi-user mesh data — pass `single_user=True`.

## Edit-mode bmesh pattern

For mesh surgery, use bmesh — not `bpy.ops.mesh.*` loops.

```python
import bpy, bmesh
ob = bpy.data.objects["SM_Crate"]
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(ob.data)
bm.verts.ensure_lookup_table()                   # required before bm.verts[i] indexing
for v in bm.verts:
    if v.co.z > 0.9:
        v.co.z += 0.1
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)   # the "merge by distance" primitive
bmesh.update_edit_mesh(ob.data)
bpy.ops.object.mode_set(mode='OBJECT')           # writes bmesh back; bm is dead after this
```

Object-mode alternative (no mode switch, good for batch work):

```python
bm = bmesh.new()
bm.from_mesh(ob.data)
# ... edit bm ...
bm.to_mesh(ob.data)
bm.free()
ob.data.update()
```

After any topology-changing `bmesh.ops.*`, re-run `ensure_lookup_table()` before indexed access. Never keep `bm` (or its verts/faces) across a mode switch or a second `execute` call — they are invalidated.

## Transforms and matrix_world

```python
import bpy, math
from mathutils import Vector
ob = bpy.data.objects["SM_Crate"]
ob.location = (2.0, 0.0, 0.5)                    # meters; 1 BU = 1 m, real-world sizes
ob.rotation_euler = (0.0, 0.0, math.radians(45)) # radians, always
ob.scale = (1.0, 1.0, 1.0)
bpy.context.view_layer.update()                  # matrix_world is lazy — update before reading
world_pos = ob.matrix_world.translation
v0_world  = ob.matrix_world @ ob.data.vertices[0].co   # local -> world
loc, rot, sca = ob.matrix_world.decompose()
```

- `location/rotation_euler/scale` are local (parent-relative). `matrix_world` is the composed world transform; writing it back-computes the locals.
- Dimensions: `ob.dimensions` = world-space bounding box size (reads scale); useful to sanity-check real-world size.

## Applying transforms

Bake scale/rotation into the mesh before UVs, modifiers that measure distances (Bevel, Solidify), and export:

```python
import bpy
ob = bpy.data.objects["SM_Crate"]
with bpy.context.temp_override(object=ob, active_object=ob,
                               selected_objects=[ob], selected_editable_objects=[ob]):
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
```

Leave `location=False` unless you want the origin moved to world zero. Negative scale flips normals — apply, then check/fix with `bmesh.ops.recalc_face_normals(bm, faces=bm.faces)`. Fails on multi-user meshes: make single-user first (`ob.data = ob.data.copy()`).

## Collections

```python
import bpy
col = bpy.data.collections.get("COL_Props")
if col is None:
    col = bpy.data.collections.new("COL_Props")
    bpy.context.scene.collection.children.link(col)
ob = bpy.data.objects["SM_Crate"]
for c in ob.users_collection:                    # an object can sit in several collections
    c.objects.unlink(ob)
col.objects.link(ob)
```

A newly created `bpy.data.objects.new(...)` object is in NO collection and thus invisible — you must link it somewhere. Follow the `COL_` naming and structure from `scene_organization`.

## Save checkpoints

Before every destructive step (apply modifiers, remesh, joins, deletes):

```python
import bpy, os
if bpy.data.filepath:
    bpy.ops.wm.save_mainfile()
else:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.expanduser("~"), "work.blend"))
```

## Common exceptions

| Error | Cause | Fix |
|---|---|---|
| `RuntimeError: Operator bpy.ops.X.poll() failed, context is incorrect` | Wrong mode, nothing selected/active, or op needs a UI area | Set selection + active + mode first; else `temp_override` with the members the op reads |
| `ReferenceError: StructRNA of type X has been removed` | Python reference held across mode switch, delete, or undo | Never cache references across risky steps — re-fetch by name (`bpy.data.objects.get`) |
| `KeyError: ... key "X" not found` | Object was auto-renamed (`.001`) or lives under a different name | Use `.get()`, print candidates, match by prefix |
| `AttributeError: 'Mesh' object has no attribute 'use_auto_smooth'` | API removed in 4.1 | `bpy.ops.object.shade_auto_smooth(angle=0.523599)` or `shade_smooth_by_angle` + `sharp_edge` edge attribute |
| `TypeError` calling an op with a dict first argument | Context-dict override removed in 4.0 | `bpy.context.temp_override(...)` |
| Stale `len(mesh.vertices)` after edit-mode ops | `ob.data` not synced while in edit mode | Read via `bmesh.from_edit_mesh`, or switch to OBJECT mode first |

## Keep scripts small and idempotent

Each `blender_execute_blender_code` call should do ONE step and be safe to re-run (calls can be retried after partial failures):

```python
import bpy
name = "SM_Crate"
ob = bpy.data.objects.get(name)                  # get-or-create, never create-blind
if ob is None:
    mesh = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(ob)
```

- Rebind by name at the top of every script; assume nothing survived from the last call.
- Print a one-line result at the end (`print(ob.name, ob.dimensions)`) — stdout comes back through the tool.
- Between steps, verify with `blender_get_scene_info` / `blender_get_object_info` / screenshot per `verify_loop`.

## Version notes

- 4.0: context-dict op override removed (`temp_override` only); Principled sockets renamed; `armature.layers` -> bone collections.
- 4.1: `use_auto_smooth` removed (see exceptions table).
- 4.2–4.5: EEVEE engine id is `'BLENDER_EEVEE_NEXT'`; 5.0 renames it back to `'BLENDER_EEVEE'`.
- 5.0: `mathutils.Vector` stores float32 (don't compare coordinates with tight float64 epsilons); `action.fcurves`/`.groups` legacy forwarders removed; `scene.node_tree` -> `scene.compositing_node_group`.

## Verify

- `blender_get_scene_info` after create/delete/rename: expected object names, no stray `.001` duplicates.
- `blender_get_object_info` after transforms: location/rotation/scale and dimensions match intent (meters, real-world sizes).
- `blender_get_viewport_screenshot` after any visible change — compare against intent per `verify_loop`.
- End state: mode is `'OBJECT'`, file saved if a destructive step just succeeded.

## Don'ts

- Don't use `bpy.ops` where direct data assignment works — ops are the #1 source of `poll()` failures.
- Don't assume selection, active object, or mode from a previous call — set all three, every time.
- Don't cache Python references to objects/meshes/bmesh across mode switches, deletes, or separate tool calls — re-fetch by name.
- Don't stack many destructive steps in one script — one step, verify, checkpoint, next.
- Don't use degrees in `rotation_euler` or centimeters for sizes — radians and meters; UEFN conversion happens at export (`uefn_export`).
- Don't create attributes with a leading `.` in the name — that namespace is reserved for Blender's hidden runtime attributes.

See also: `scene_organization`, `verify_loop`, `modifiers`, `mesh_cleanup`, `uefn_export`.
