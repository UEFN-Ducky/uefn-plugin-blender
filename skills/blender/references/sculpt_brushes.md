# Sculpt brushes — scripted strokes & masked filters

Drive Blender's REAL sculpt brushes (Smooth, Crease Sharp, Clay, Grab…) headless. Two engines, always try in this order:

1. **Mesh filters + masks** — deterministic, no mouse math, works every time. Covers 80% of "brush" asks (smooth this face, inflate this patch, sharpen detail).
2. **Scripted brush strokes** — `bpy.ops.sculpt.brush_stroke` with synthesized stroke points. Full brush engine (pinch falloff, clay buildup) but view-dependent: frame the viewport first.

Load after `sculpting` (remesh/multires prep). Brushes need vertex density — a stroke on an 8-vert cube does nothing. Voxel-remesh first (`sculpting`), sculpt, then `retopology`.

## Brush picker

| Goal | Brush (Essentials) | Deterministic fallback |
|---|---|---|
| Smooth faces / soften lumps | **Smooth** (or any brush with `mode='SMOOTH'`) | `mesh_filter SURFACE_SMOOTH` + mask |
| Thin deep pinch line (nostril crease, cloth fold) | **Crease Sharp** | edge crease + Subsurf (`organic_forms`) |
| Build up volume (muscle, clay pass) | **Clay** / **Clay Strips** | proportional `transform.translate` |
| Sharp cut / scar line | **Draw Sharp** | — |
| Move a mass (nose, brow) | **Grab** / **Elastic Grab** | proportional translate (preferred) |
| Puff out / suck in | **Inflate/Deflate** | `mesh_filter INFLATE` |
| Flatten a plane (forehead, panel) | **Flatten/Contrast** | `mesh_filter SMOOTH` high strength |
| Pull a horn/tentacle out | **Snake Hook** | Skin modifier spine (`organic_forms`) |
| Polish hard-surface facets | **Scrape/Fill** | — |

Rule stays ponytail: if the fallback column does the job, use it — strokes are for when you need real brush falloff/buildup character.

## Setup — sculpt mode + viewport helpers

Paste once per session:

```python
import bpy
from bpy_extras import view3d_utils

def sculpt_ctx():
    win = bpy.context.window_manager.windows[0]
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    region = next(r for r in area.regions if r.type == 'WINDOW')
    return dict(window=win, area=area, region=region,
                space_data=area.spaces.active, region_data=area.spaces.active.region_3d)

def enter_sculpt(ob, frame='FRONT'):
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='SCULPT')
    with bpy.context.temp_override(**sculpt_ctx()):
        bpy.ops.view3d.view_axis(type=frame)   # 'FRONT'|'RIGHT'|'TOP'…
        bpy.ops.view3d.view_selected()         # strokes project through this view
```

Framing matters: stroke `mouse` coords are projected through the 3D view. Off-screen points silently miss.

## Activate a brush

4.3+ ships brushes as **Essentials assets** (they are NOT in `bpy.data.brushes` until activated). 4.2 still uses `paint.brush_select`.

```python
def activate_brush(name):
    """name: exact Essentials label, e.g. 'Crease Sharp', 'Smooth', 'Clay Strips'."""
    with bpy.context.temp_override(**sculpt_ctx()):
        try:                                   # 4.3 → 5.0
            bpy.ops.brush.asset_activate(
                asset_library_type='ESSENTIALS',
                relative_asset_identifier=
                    f"brushes/essentials_brushes-mesh_sculpt.blend/Brush/{name}")
        except Exception:                      # ≤ 4.2 fallback: enum tool name
            bpy.ops.paint.brush_select(
                sculpt_tool=name.split()[0].upper(), toggle=False)
    return bpy.context.tool_settings.sculpt.brush

br = activate_brush("Crease Sharp")
print(br.name)                                 # confirm before stroking
```

Size and strength — lock size to **scene units** so zoom level can't change the result:

```python
ups = bpy.context.scene.tool_settings.unified_paint_settings
ups.use_unified_size = True
ups.use_locked_size = 'SCENE'
ups.unprojected_radius = 0.04     # brush radius in meters — the real "brush size"
br.strength = 0.5                 # 0..1; several weak passes beat one strong one
```

## Fire a stroke

Sample points ON the surface, project to 2D, emit dense stroke elements:

```python
from mathutils import Vector

def surface_path(ob, p_from, p_to, n=32):
    """Straight path in world space snapped onto the mesh surface."""
    inv = ob.matrix_world.inverted()
    pts = []
    for i in range(n):
        p = Vector(p_from).lerp(Vector(p_to), i / (n - 1))
        hit, loc, _n, _i = ob.closest_point_on_mesh(inv @ p)
        if hit:
            pts.append(ob.matrix_world @ loc)
    return pts

def stroke(points_world, mode='NORMAL', pressure=1.0):
    """mode: 'NORMAL' | 'INVERT' (e.g. deflate) | 'SMOOTH' (any brush smooths)."""
    ctx = sculpt_ctx()
    elems = []
    for p in points_world:
        m = view3d_utils.location_3d_to_region_2d(ctx["region"], ctx["region_data"], p)
        if m is None:
            continue                           # behind camera / off-screen — reframe!
        elems.append({"name": "", "location": tuple(p),
                      "mouse": (m.x, m.y), "mouse_event": (m.x, m.y),
                      "pressure": pressure, "size": 50,
                      "pen_flip": False, "x_tilt": 0.0, "y_tilt": 0.0})
    assert len(elems) >= max(2, len(points_world) // 2), "stroke mostly off-screen — reframe view"
    with bpy.context.temp_override(**ctx):
        bpy.ops.sculpt.brush_stroke(stroke=elems, mode=mode)

# Example: crease line across a forehead
ob = bpy.context.active_object
enter_sculpt(ob, frame='FRONT')
activate_brush("Crease Sharp")
stroke(surface_path(ob, (-0.05, -0.2, 1.72), (0.05, -0.2, 1.72)))
```

- 24–48 points per stroke; brushes apply per-sample, so sparse strokes stutter.
- **Grab / Snake Hook** move mass from first→last sample: give them the full drag path, one stroke per pull.
- `mode='SMOOTH'` smooths with ANY active brush — quick soften without switching.
- Screenshot after every 1–3 strokes (`verify_loop`); undo is `bpy.ops.ed.undo()` per stroke.

## Masks + mesh filters — the reliable "smooth this face" recipe

Masking = telling the brush WHERE. Mask value 1.0 **protects**, 0.0 is sculptable. Write it per-vertex, then filter — deterministic brush-quality smoothing:

```python
import bpy
ob = bpy.data.objects["SM_Head"]
bpy.context.view_layer.objects.active = ob
bpy.ops.object.mode_set(mode='OBJECT')        # attribute writes in object mode
me = ob.data
mask = me.attributes.get(".sculpt_mask") or me.attributes.new(".sculpt_mask", 'FLOAT', 'POINT')

def editable(co):                             # cheeks/forehead region, object space
    return co.z > 1.5 and co.y < 0.02
for v in me.vertices:
    mask.data[v.index].value = 0.0 if editable(v.co) else 1.0

bpy.ops.object.mode_set(mode='SCULPT')
with bpy.context.temp_override(**sculpt_ctx()):
    bpy.ops.sculpt.mesh_filter(type='SURFACE_SMOOTH', strength=1.0, iteration_count=4)
    bpy.ops.paint.mask_flood_fill(mode='VALUE', value=0.0)   # clear mask when done
```

Filter types worth knowing: `SMOOTH` (volume-shrinking), `SURFACE_SMOOTH` (keeps volume — use for faces), `INFLATE`, `SHARPEN`, `RELAX` (evens triangles, no shape change), `ENHANCE_DETAILS`. Strength small + more iterations = controllable.

Whole-mesh soften (no mask): flood-fill mask to 0, run `SMOOTH` at `strength=0.3, iteration_count=2`.

## Recipe — smooth, clean face from a lumpy head

1. `sculpting`: voxel remesh ~5 mm (`remesh_voxel_size=0.005`) for even density.
2. Mask recipe above → `SURFACE_SMOOTH` on cheeks/forehead (keeps nose/lips crisp).
3. Detail passes: `Crease Sharp` strokes for eyelid/nostril lines, `Clay Strips` (`strength≈0.3`) for brow/cheekbone volume.
4. Whole-mesh `SMOOTH` filter at `strength=0.2` to unify.
5. Screenshot front/side/3-quarter (`verify_loop`) → iterate.
6. It's still a sculpt: `retopology` (+ `face_topology` loops) before UEFN.

## Verify

- `print(bpy.context.tool_settings.sculpt.brush.name)` matches what you meant to activate.
- Screenshot before/after each stroke batch — a stroke that projected off-screen fails silently.
- `blender_get_object_info` vert count unchanged by strokes (brushes move verts, never add — except dyntopo, which stays off).
- Mask cleared (`mask_flood_fill value=0`) before the next tool.

## Don'ts

- Don't stroke without `enter_sculpt(..., frame=...)` — unframed views project garbage.
- Don't use pixel brush size headless — lock `use_locked_size='SCENE'` + `unprojected_radius`.
- Don't sculpt low-poly base meshes — remesh first, brushes need density.
- Don't chain 50 micro strokes to fix proportions — that's `blockout` / proportional edits.
- Don't leave dyntopo on during scripted strokes (topology changes mid-loop); use voxel remesh checkpoints.
- Don't skip `bpy.ops.wm.save_mainfile()` before a stroke experiment.

See also: `sculpting`, `organic_forms` (deterministic fallbacks), `face_topology`, `retopology`, `verify_loop`.
