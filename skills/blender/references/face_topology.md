# Face topology

Animation-ready facial topology: loop anatomy, pole placement, budgets, a ring-out build order that is fully scriptable, deformation testing, and the retopo path for sculpted/AI-generated heads. Load when building or fixing a head that must blink, talk, or emote.

## Loop anatomy — what must exist

The face deforms along two ring muscles: **orbicularis oculi** (eye) and **orbicularis oris** (mouth). Topology mirrors them as concentric rings; everything else connects or fills.

| Structure | Minimum | Purpose |
|---|---|---|
| Eye rings | **3 concentric loops** per eye (4 for hero) | blink, squint, brow-raise without shearing |
| Lid rim loop | 1, exactly on the lid margin | crisp lid edge; second loop just behind it gives lid thickness |
| Upper-lid crease loop | 1 | the fold when the eye opens |
| Mouth rings | **3 concentric loops** (4–5 for wide expression range) | smile, pucker, jaw-open |
| Lip-edge loop | 1 on the lip margin + at least 1 continuing inside to the mouth bag | clean lip line; no tearing when mouth opens |
| **Mask loop** | 1 loop encircling both eyes and the mouth as one ring | isolates the mobile face from the static skull; expressions stop at it |
| Nasolabial loop | nostril base → around mouth corner → chin | the smile fold deforms along it instead of across it |
| Jaw loop | chin → ear along the jawline | jaw-open support |

Mobile/stylized heads may drop to 2 eye rings and 2 mouth rings — accept the reduced expression range consciously, don't drift into it.

## Poles

A pole is any vert with valence != 4. **E-pole** = 5 edges, **N-pole** = 3 edges. Both pinch under subdivision and dimple under deformation, so park them where the skin barely moves.

| Put poles here | Never here |
|---|---|
| Temple | Lid rim or any eye ring |
| Jaw corner (below the ear) | Lip margin / lip corners |
| Base of the nostril (the classic spot) | Nasolabial fold itself |
| Under the chin, behind the ear, scalp | Cheek mass over the smile |

The mouth corner wants to be a 5-pole where the rings collapse — offset it **outward into the cheek**, off the lip margin, so the pucker/smile zone stays pure quads. Valence-6 verts: keep them out of deforming areas entirely.

## Quad-only and budgets

Quads define unambiguous loops/rings, subdivide predictably (Catmull-Clark), and skin cleanly. **No n-gons anywhere; no triangles in the eye/mouth regions.** Triangles are tolerable only in hidden flat zones: behind the ear, scalp under hair, inside the mouth bag.

| Tier | Face-region budget |
|---|---|
| Mobile / stylized | 200–500 faces |
| AAA PC/console face | 5,000–15,000 faces |
| MetaHuman head (reference ceiling) | 24k verts LOD0 → 12k / 6k / 2.5k … 130 at LOD7 |

For UEFN heads, treat MetaHuman LOD1–LOD2 (≈6k–12k verts) as the practical ceiling; the LOD0 numbers are cinematic-hero territory. Work in meters — a Fortnite character is ≈1.9 m tall, so an eye aperture is ≈0.03 m wide.

## Build order (ring-out method, scriptable)

Rings first, connect second, fill last. Model the left half only.

### 1. Mirror setup

```python
import bpy
ob = bpy.context.object
mir = ob.modifiers.new("Mirror", 'MIRROR')
mir.use_axis[0] = True
mir.use_clip = True            # locks center-seam verts to X=0 - no manual welding later
mir.merge_threshold = 0.0005
```

### 2. Eye and mouth rings

```python
def concentric_rings(name, verts, radius, rings, growth=1.4, location=(0, 0, 0)):
    bpy.ops.mesh.primitive_circle_add(vertices=verts, radius=radius, location=location)
    ob = bpy.context.object
    ob.name = name
    bpy.ops.object.mode_set(mode='EDIT')
    for _ in range(rings):
        bpy.ops.mesh.extrude_region_move()          # duplicate the boundary loop, quad-bridged
        bpy.ops.transform.resize(value=(growth,) * 3)
    bpy.ops.object.mode_set(mode='OBJECT')
    return ob

eye   = concentric_rings("eye_L",  16, 0.016, 3, location=(0.032, -0.11, 1.63))
mouth = concentric_rings("mouth",  16, 0.025, 3, location=(0.0,   -0.115, 1.56))
```

16 verts per ring is the game-res sweet spot (8 is too coarse for a blink; 24+ only for hero closeups). Shape the flat rings against reference afterwards (eye almond, lip bow) with proportional edits — flow survives any shaping.

### 3. Bridge rings together

Join, then bridge the open boundary loops. `select_non_manifold` grabs every open boundary, so isolate to two loops per bridge pass.

```python
bpy.ops.object.select_all(action='DESELECT')
eye.select_set(True); mouth.select_set(True)
bpy.context.view_layer.objects.active = mouth
bpy.ops.object.join()

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_mode(type='EDGE')
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.mesh.select_non_manifold()                  # open boundary loops
bpy.ops.mesh.bridge_edge_loops(type='PAIRS', number_cuts=2, interpolation='SURFACE')
```

`number_cuts` inserts intermediate loops during the bridge — cheap way to seed cheek density. The bridge between the outer eye ring and outer mouth ring becomes the mask-loop zone; route the nasolabial loop through it (nostril base → mouth corner).

### 4. Fill brow / cheek / jaw patches

Grid Fill wants a single closed boundary with an even edge count and matching opposite sides.

```python
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.mesh.select_non_manifold()                  # remaining hole boundary
bpy.ops.mesh.fill_grid(span=4, offset=0)            # tune span until the grid runs with the flow
```

Fill order: brow band above the eye rings, cheek between mask loop and jaw loop, then jaw/neck. After each fill, check the flow — `offset` rotates which corner the grid anchors to.

### 5. Insert loops where density is short

`bpy.ops.mesh.loopcut_slide` needs an interactive VIEW_3D region — avoid it in automation. The scriptable loop cut: select one edge crossing the flow, expand to the ring, subdivide.

```python
me = bpy.context.object.data
bpy.ops.object.mode_set(mode='OBJECT')
for e in me.edges: e.select = False
me.edges[edge_index].select = True                  # one edge perpendicular to the wanted loop
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.loop_multi_select(ring=True)           # expand to the full edge ring
bpy.ops.mesh.subdivide(number_cuts=1)               # inserts the new loop
```

## Deformation testing

Test **before** rigging. Two scriptable probes; screenshot each pose.

### Temporary shape key (jaw-open test)

```python
ob = bpy.context.object
ob.shape_key_add(name="Basis", from_mix=False)
key = ob.shape_key_add(name="TEST_jaw_open", from_mix=False)
from mathutils import Vector
for v in ob.data.vertices:
    if v.co.z < 1.58 and v.co.y < -0.09:            # crude chin/lower-lip mask; vertex group in practice
        key.data[v.index].co += Vector((0.0, -0.004, -0.02))
key.value = 1.0
# screenshot, inspect, then remove the probe:
ob.shape_key_remove(key)
ob.shape_key_remove(ob.data.shape_keys.key_blocks["Basis"])
```

### Proportional grab (smile / blink test)

```python
me = bpy.context.object.data
bpy.ops.object.mode_set(mode='OBJECT')
me.vertices[mouth_corner_idx].select = True
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.transform.translate(value=(0.004, 0.0, 0.006),
    use_proportional_edit=True, proportional_edit_falloff='SMOOTH',
    proportional_size=0.03,
    use_proportional_connected=True)                # stops the upper lip dragging the lower
# inspect, then undo the probe:
bpy.ops.ed.undo()
```

Failures read instantly: pinching = pole in the deform zone; faceting = missing ring; lip tearing = no mouth-bag loop; cheek collapsing = mask loop broken.

## Retopo path from sculpt / AI-generated heads

Generated and sculpted heads never have deformation loops. Do not ship them raw.

```python
# 1. Clean the source: watertight, even density
src = bpy.data.objects["scan_head"]
src.data.remesh_voxel_size = 0.004
src.data.use_remesh_fix_poles = True
src.data.use_remesh_preserve_volume = True
with bpy.context.temp_override(object=src, active_object=src, selected_objects=[src]):
    bpy.ops.object.voxel_remesh()

# 2. Wrap a loop-correct template head (built with the ring method above) onto it
tmpl = bpy.data.objects["basemesh_head"]
sw = tmpl.modifiers.new("Wrap", 'SHRINKWRAP')
sw.target = src
sw.wrap_method = 'TARGET_PROJECT'                   # best-behaved wrap for organic surfaces
sw.wrap_mode = 'ON_SURFACE'
with bpy.context.temp_override(object=tmpl, active_object=tmpl, selected_objects=[tmpl]):
    bpy.ops.object.modifier_apply(modifier=sw.name)
```

Template + shrinkwrap is the **only fully scriptable loop-correct retopo**: topology from the template, shape from the sculpt. Fix drift (lid rims, lip line) with proportional grabs after the wrap. `bpy.ops.object.quadriflow_remesh(mode='FACES', target_faces=4000)` gives uniform quads but **no edge-flow awareness** — usable for mid-LODs, never for final facial topology.

## Version notes

- Every operator above is identical across 4.2 LTS → 5.0. Blender 5.0's shape-key overhaul (Make Basis, multi-select, drag-reorder) is UI-side; `shape_key_add` / `shape_key_remove` are unchanged.
- Merge-by-distance welding (rarely needed with `use_clip` mirroring) is `bmesh.ops.remove_doubles` in scripts; there is no `bpy.ops.mesh.merge_by_distance` operator in 4.2–5.0.

## Verify

- `blender_get_viewport_screenshot` front + 3/4 view in wireframe-over-solid: rings read as clean concentric circles around eye and mouth; nasolabial line visible as a loop, not a zigzag.
- Screenshot each deformation probe (jaw open, smile, blink): no pinching, tearing, or faceting.
- `blender_get_object_info` on the head: vert count inside the tier budget; then confirm quad-only in the eye/mouth region (select the mask area, `bpy.ops.mesh.select_face_by_sides(number=4, type='NOTEQUAL', extend=False)` — expect zero selected).
- Poles: spot-check valence at lip corners and lid rims via bmesh (`len(v.link_edges)`); anything != 4 there is a defect.

## Don'ts

- No poles on the lid rim or lip margin; offset the mouth-corner 5-pole into the cheek.
- No triangles across the eyelid or lips; no n-gons anywhere on the head.
- Don't skip the mouth-bag loop — the first jaw-open test will tear the lips.
- Don't run Quadriflow (or any auto-remesher) as final face topology; it has no loop awareness.
- Don't ship a head without running the shape-key/proportional probes — rigging is too late to discover flow errors.
- Don't use `bpy.ops.mesh.loopcut_slide` headless; ring-select + subdivide instead.

See also: `retopology`, `body_anatomy`, `shape_keys`, `verify_loop`.
