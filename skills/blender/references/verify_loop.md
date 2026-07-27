# Verify loop

Screenshot-compare discipline for every modeling session: when to call `blender_get_viewport_screenshot`, how to rig the viewport via bpy so screenshots actually carry information, and what "done" means. Load this once per session and apply it throughout.

## The loop

Change → `blender_get_viewport_screenshot` → compare vs intent/reference → fix in small bpy steps → screenshot again. Never chain many blind edits: each screenshot costs seconds, a wrong mesh costs the session.

| After | Screenshot with | Looking for |
|---|---|---|
| Blockout / primitives placed | SOLID, 3/4 view, stats overlay | Proportions, scale vs neighbors |
| Boolean / bevel / mirror / subsurf | Cavity matcap + wireframe overlay | Pinches, shading artifacts, edge flow |
| Normal edits, flipped-looking faces | Face-orientation overlay | Red (inward) faces |
| Materials assigned | `MATERIAL` preview shading | Slot assignment, tiling, roughness read |
| Any destructive apply (modifier, remesh, join) | Before AND after | Silhouette unchanged where it should be |
| Rename / collection moves only | `blender_get_scene_info` instead | No pixels needed for bookkeeping |

Each `blender_execute_blender_code` call runs standalone — re-paste small helpers per call; don't rely on variables surviving between calls.

## Viewport handle (paste at top of camera/shading snippets)

```python
import bpy

def view3d():
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            region = next(r for r in area.regions if r.type == 'WINDOW')
            return area, region, area.spaces.active
    raise RuntimeError("No 3D viewport open")

area, region, space = view3d()
```

## Shading modes — pick the one that answers your question

| Question | `space.shading` setup |
|---|---|
| Is the form right? | `type='SOLID'`, `light='MATCAP'`, `color_type='SINGLE'` (kill color noise) |
| Surface quality / panel lines? | Solid + `show_cavity=True`, `cavity_type='BOTH'` |
| Topology sane? | `type='WIREFRAME'`, or better: wireframe overlay on shaded (below) |
| Normals smooth/hard where intended? | Matcap `'check_normal+y.exr'` |
| Do materials read? | `type='MATERIAL'` (EEVEE preview, no engine setup needed) |
| Final look / lighting? | `type='RENDERED'` (needs `scene.render.engine`, see Version notes) |

```python
sh = space.shading
sh.type = 'SOLID'              # 'WIREFRAME' | 'SOLID' | 'MATERIAL' | 'RENDERED'
sh.light = 'MATCAP'            # 'STUDIO' | 'MATCAP' | 'FLAT'
sh.studio_light = 'basic_1.exr'
sh.color_type = 'SINGLE'       # 'MATERIAL'/'RANDOM' when you need per-object separation
sh.show_cavity = True
sh.cavity_type = 'BOTH'        # ridges + valleys pop bevels and pinch errors
```

## Camera control — make the angle deliberate

Frame the subject first (ops need a viewport context override):

```python
bpy.ops.object.select_all(action='DESELECT')
ob = bpy.data.objects["SM_Crate"]
ob.select_set(True)
bpy.context.view_layer.objects.active = ob

with bpy.context.temp_override(area=area, region=region):
    bpy.ops.view3d.view_axis(type='FRONT')   # 'TOP'/'BOTTOM'/'LEFT'/'RIGHT'/'BACK'
    bpy.ops.view3d.view_selected()           # frame selected = fills the screenshot
```

Or rig the view directly through `region_3d` — no override needed, fully deterministic:

```python
import math
from mathutils import Euler
r3d = space.region_3d
r3d.view_perspective = 'ORTHO'   # ortho for proportion checks; 'PERSP' for presentation
r3d.view_rotation = Euler((math.radians(75), 0, math.radians(45)), 'XYZ').to_quaternion()  # 3/4
```

Cluttered scene? Isolate: `bpy.ops.view3d.localview(frame_selected=True)` inside the same `temp_override` (run again to exit), or `other_ob.hide_set(True)` per object. A screenshot of the wrong object verifies nothing.

## Turntable check

One `blender_execute_blender_code` to set the angle, then one `blender_get_viewport_screenshot`, per view. Minimum for signing off any asset: front, side, 3/4, top.

| View | `view_rotation` Euler (deg, XYZ) | Or `view_axis(type=...)` |
|---|---|---|
| Front | (90, 0, 0) | `'FRONT'` |
| Right | (90, 0, 90) | `'RIGHT'` |
| Back | (90, 0, 180) | `'BACK'` |
| Left | (90, 0, -90) | `'LEFT'` |
| 3/4 hero | (75, 0, 45) | — |
| Top | (0, 0, 0) | `'TOP'` |

```python
import math
from mathutils import Euler
_, _, space = view3d()
space.region_3d.view_rotation = Euler(
    (math.radians(90), 0, math.radians(90)), 'XYZ').to_quaternion()   # right view
# ...then call blender_get_viewport_screenshot, repeat for the next angle
```

Characters and creatures get all four sides plus top; props can often pass on front/side/3-4; environments add a high 3/4 (Euler X ≈ 55°) for layout reads.

## Overlays for review passes

```python
ov = space.overlay
ov.show_overlays = True
ov.show_wireframes = True          # wireframe ON TOP of shaded = topology review mode
ov.wireframe_threshold = 1.0       # 1.0 shows every edge
ov.wireframe_opacity = 0.75
ov.show_face_orientation = True    # blue = outward, red = flipped normals
ov.show_stats = True               # Objects/Verts/Faces/Tris readout in the screenshot corner
```

Turn `show_wireframes` and `show_face_orientation` OFF again before form/beauty screenshots — they hide the silhouette read.

## Numbers beat pixels

Screenshots can't measure. Pair them with hard data:

```python
import bpy
dg = bpy.context.evaluated_depsgraph_get()
for ob in bpy.context.selected_objects:
    if ob.type != 'MESH':
        continue
    ob_eval = ob.evaluated_get(dg)
    me = ob_eval.to_mesh()                                # includes modifier results
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    print(f"{ob.name}: {len(me.vertices)} v / {len(me.polygons)} f / {tris} tris, "
          f"dims {tuple(round(d, 3) for d in ob.dimensions)} m")
    ob_eval.to_mesh_clear()
```

- `ob.dimensions` vs real-world targets: UEFN character ≈ 1.9 m, door ≈ 2.1 m, building tile 5.12 m.
- Tri counts vs budget before export — the stats overlay shows the same numbers in-frame, but printing survives in the tool result.
- `blender_get_object_info` / `blender_get_scene_info` for transforms, modifiers, and hierarchy without touching pixels.

## Comparing against a user reference

- Re-view the user's reference image before every compare — don't trust memory of it.
- Match the camera to the reference: orthographic front/side for blueprint sheets (`view_perspective='ORTHO'` + `view_axis`), perspective 3/4 for concept paintings.
- Compare silhouettes first (matcap, single color), then proportions by measured ratios (e.g. head-to-height, wheelbase-to-length) using `ob.dimensions` and vertex positions — not eyeballing.
- Log each mismatch as a concrete edit ("nose 15% too long", "roof line flat, ref curves") before touching the mesh. Full workflow: `reference_match`.

## Version notes

- Viewport shading, overlay, and `region_3d` APIs above are stable across 4.2 LTS → 5.0.
- `RENDERED` shading only: the EEVEE engine id is `'BLENDER_EEVEE_NEXT'` in 4.2–4.5 and renamed back to `'BLENDER_EEVEE'` in 5.0. Guard:

```python
try:
    bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'   # 4.2–4.5
except TypeError:
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'        # 5.0
```

## Verify — what "done" looks like

An asset is done when, with no cherry-picked angle:

- All four turntable views pass in solid-matcap: silhouette reads, proportions match reference/brief, scale sane next to a known-size object.
- Cavity + wireframe-overlay pass shows no pinches, no stretched n-gons in visible areas, no shading artifacts.
- Face-orientation overlay shows zero red on renderable geometry.
- Stats/printed counts within budget; `ob.dimensions` within tolerance of target size.
- Names and collections still follow `scene_organization` conventions (`SM_`/`SK_`/`COL_`).
- The final 3/4 hero screenshot was taken AFTER the last edit — never declare done on a stale image.

## Don'ts

- Don't chain 10 modeling steps blind, then screenshot once — you can't tell which step broke it.
- Don't screenshot the default random angle: set shading + camera first or the image answers nothing.
- Don't judge topology from a beauty shot or forms from a wireframe — one question per screenshot setup.
- Don't read tri counts off pixels when you can print exact evaluated counts.
- Don't leave review overlays (wireframe, face orientation) on for silhouette/beauty compares.
- Don't declare done without a fresh screenshot when the user can see the viewport — they will look.

See also: `reference_match`, `asset_qa`, `scene_organization`, `bpy_fundamentals`.
