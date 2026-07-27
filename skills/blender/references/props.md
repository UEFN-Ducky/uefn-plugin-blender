# Props

Game props for UEFN: crates, barrels, furniture, lanterns, tools. Load this for any standalone object that isn't a character, vehicle, or modular kit piece. Everything runs through `blender_execute_blender_code`; verify with `blender_get_viewport_screenshot` and `blender_get_object_info`.

## Pipeline (compressed)

1. **Real dimensions** from reference — block the bounding volume first (`blockout`).
2. **Mid-poly detail** — real chamfers, no subdivision support loops (`hard_surface` for complex forms).
3. **Bevel + Weighted Normal** — shading lives on the chamfer, not in a bake.
4. **UV at target texel density**, one material or trim sheet (`uv_workflow`, `materials_shading`).
5. **Origin** at base or grab point, `SM_` name, apply transforms.
6. **Quick QA** → `asset_qa` → `lod_collision` → `uefn_export`.

## 1. Real dimensions first

Work in meters, scale 1.0. Wrong scale poisons everything downstream (bevel widths, texel density, UEFN import at 1 uu = 1 cm).

| Reference object | Size (m) |
|---|---|
| Character capsule (Fortnite) | 1.92 tall |
| Door | 2.1 tall |
| Wooden crate | 0.4–0.6 cube |
| Barrel (cask) | ~0.9 tall × 0.6 belly dia |
| Table top / chair seat | 0.75 / 0.45 high |
| Handheld lantern | 0.25–0.3 tall |
| Building tile | 5.12 (512 uu) |

```python
import bpy
ob = bpy.context.object
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
print(ob.name, [round(d, 3) for d in ob.dimensions])  # compare to the table
```

## 2. UEFN budgets (LOD0, Epic best-practices)

| Prop size | Simple | Medium detail | Complex | Vert cap |
|---|---|---|---|---|
| Small (≤ ½ character) | 400 | 700 | 1,200 | 1,000 |
| Medium (≈ character) | 900 | 2,000 | 4,000 | 3,000 |
| Large | 2,500 | 6,000 | 9,000 | 5,000 |

Ship **3 LODs minimum** (typical prop chain: 900–3,200 verts → 60–250 at LOD3). Textures ≤ 2K power-of-two. **One material section per mesh** preferred, ≤ 10 UCX collision primitives — see `lod_collision`.

## 3. Mid-poly + weighted normals

The 2026 norm for props: model real chamfers on visible edges, then bend vertex normals toward the large flat faces so the shading transition sits entirely on the bevel. Normal maps become optional micro-detail. No support loops, no high→low bake for most props (bake only hero pieces — `texture_bake`).

Chamfer widths that read at gameplay distance:

| Edge type | Width | Segments |
|---|---|---|
| Structural edges, large props | 8–15 mm | 1–2 |
| Panel/medium edges | 4–8 mm | 1–2 |
| Small hardware (handles, hinges) | 2–4 mm | 1 |
| Under ~2 mm | skip geometry — texture carries it | — |

```python
import bpy, math
ob = bpy.context.object
bev = ob.modifiers.new("Bevel", 'BEVEL')
bev.width = 0.006                 # 6 mm — reads at 2–5 m
bev.segments = 2
bev.limit_method = 'ANGLE'
bev.angle_limit = math.radians(40)
wn = ob.modifiers.new("WeightedNormal", 'WEIGHTED_NORMAL')
wn.mode = 'FACE_AREA'
wn.keep_sharp = True
# smooth shading + sharp_edge attribute, no extra modifier (4.1+; unchanged in 5.0)
bpy.ops.object.shade_smooth_by_angle(angle=math.radians(60), keep_sharp_edges=True)
```

Prefer `shade_smooth_by_angle` (writes the `sharp_edge` attribute directly) over `shade_auto_smooth` (adds a "Smooth by Angle" node-group modifier you'd have to apply before export).

## 4. Texel density + material count

Anchor: a 2K texture over one 5.12 m building tile = **400 px/m (4 px/cm)**.

- Standard props: **400–512 px/m**
- Hero / held-in-hand: up to **800 px/m**
- Background clutter: **200–256 px/m**

Keep density consistent across a prop set — mismatched blur/sharpness reads worse than lower uniform density. One material per prop; families of props (dock set, kitchen set) share a **trim sheet** so the whole set stays at one material and one texture fetch. Unique-unwrap + bake only for hero props. Details: `uv_workflow`, `materials_shading`.

## 5. Origin placement

The origin is the snap/attach point in UEFN — never leave it at the world center or volume center.

- **Floor-standing** (crate, barrel, furniture): bottom-center.
- **Wall-mounted**: on the back contact face.
- **Handheld / hung** (lantern, tools): the grab or hang point.

```python
import bpy
from mathutils import Vector
ob = bpy.context.object
bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
bpy.context.scene.cursor.location = (sum(v.x for v in bb) / 8,
                                     sum(v.y for v in bb) / 8,
                                     min(v.z for v in bb))   # bottom-center
bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
```

## 6. Quick QA

```python
import bpy, bmesh
ob = bpy.context.object
me = ob.data
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.0005)
ngons = sum(1 for f in bm.faces if len(f.verts) > 4)
loose = sum(1 for v in bm.verts if not v.link_faces)
bm.to_mesh(me); bm.free(); me.update()
tris = sum(len(p.vertices) - 2 for p in me.polygons)
print(f"verts={len(me.vertices)} tris={tris} ngons={ngons} loose={loose} "
      f"mats={len(ob.material_slots)} scale={tuple(ob.scale)}")
```

Verts under the size cap, ngons 0 (or triangulated at export), loose 0, mats 1 (2 max with a justified emissive), scale (1,1,1). Full checklist: `asset_qa`.

## Micro-example: crate (0.5 m)

```python
import bpy, math
bpy.ops.mesh.primitive_cube_add(size=1)
crate = bpy.context.object; crate.name = "SM_Crate"
crate.dimensions = (0.5, 0.5, 0.5)
bpy.ops.object.transform_apply(scale=True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.inset(thickness=0.035, depth=-0.008, use_individual=True)  # plank frame
bpy.ops.object.mode_set(mode='OBJECT')
bev = crate.modifiers.new("Bevel", 'BEVEL')
bev.width = 0.004; bev.segments = 1
bev.limit_method = 'ANGLE'; bev.angle_limit = math.radians(40)
wn = crate.modifiers.new("WN", 'WEIGHTED_NORMAL'); wn.mode = 'FACE_AREA'; wn.keep_sharp = True
bpy.ops.object.shade_smooth_by_angle(angle=math.radians(60), keep_sharp_edges=True)
```

## Micro-example: barrel (0.9 × 0.6 m)

```python
import bpy, bmesh, math
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.24, depth=0.9)
barrel = bpy.context.object; barrel.name = "SM_Barrel"
bm = bmesh.new(); bm.from_mesh(barrel.data)
side = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 0.1]
bmesh.ops.subdivide_edges(bm, edges=side, cuts=3)          # 3 belly rings
for v in bm.verts:
    t = max(0.0, 1.0 - (abs(v.co.z) / 0.45) ** 2)          # parabolic belly
    s = 1.0 + 0.25 * t                                     # +25% at the middle
    v.co.x *= s; v.co.y *= s
bm.to_mesh(barrel.data); bm.free()
hoops = []
for z in (-0.28, 0.28):                                    # metal hoops
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.285, depth=0.04,
                                        location=(0, 0, z))
    hoops.append(bpy.context.object)
objs = [barrel] + hoops
with bpy.context.temp_override(active_object=barrel, selected_objects=objs,
                               selected_editable_objects=objs):
    bpy.ops.object.join()
# then: Bevel (3 mm) + WeightedNormal + shade_smooth_by_angle as in §3
```

## Micro-example: lantern (0.28 m, emissive)

```python
import bpy, math
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.07, depth=0.16,
                                    location=(0, 0, 0.11))          # glass body
body = bpy.context.object; body.name = "SM_Lantern"
bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.085, radius2=0.02,
                                depth=0.06, location=(0, 0, 0.22))  # cap
cap = bpy.context.object
bpy.ops.mesh.primitive_torus_add(major_radius=0.03, minor_radius=0.006,
                                 major_segments=16, minor_segments=6,
                                 location=(0, 0, 0.27),
                                 rotation=(math.radians(90), 0, 0))  # hang ring
ring = bpy.context.object
objs = [body, cap, ring]
with bpy.context.temp_override(active_object=body, selected_objects=objs,
                               selected_editable_objects=objs):
    bpy.ops.object.join()
mat = bpy.data.materials.new("M_Lantern_Glow")
mat.use_nodes = True          # 5.0: deprecated no-op (always on); required in 4.x
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Emission Color"].default_value = (1.0, 0.72, 0.35, 1.0)
bsdf.inputs["Emission Strength"].default_value = 20.0
body.data.materials.append(mat)
```

Emissive glass as a second material slot is the one accepted exception to one-material; for non-hero lanterns, pack the glow into the single material's Emission socket via a mask instead. Origin: base if it sits on tables, ring top if it hangs — set per placement intent (§5).

## Version notes

- Every modifier and operator above is identical across 4.2 LTS → 5.0.
- If you kitbash with booleans on 5.0: `BooleanModifier.solver` enum `'FAST'` was renamed `'FLOAT'` (`'EXACT'` unchanged).
- `material.use_nodes` is deprecated in 5.0 (always True, removal planned 6.0) — setting it stays harmless.

## Verify

- `blender_get_viewport_screenshot` from a ¾ view at gameplay distance (3–5 m): chamfer highlights visible on every major edge, no faceting on flats, no black shading artifacts (bad normals).
- `blender_get_object_info`: dimensions match the reference table; vert count under the §2 cap.
- QA snippet (§6) prints ngons 0, loose 0, mats ≤ 2, scale (1,1,1).
- Screenshot next to a 1.92 m reference box — the prop must read at the right scale.

## Don'ts

- Don't model at arbitrary size and plan to "fix scale at export" — real meters from the first primitive.
- Don't use subdivision + support loops for game props — mid-poly chamfers + weighted normals.
- Don't use one bevel width everywhere; edge size hierarchy is what makes a prop read as manufactured.
- Don't touch `mesh.use_auto_smooth` / `auto_smooth_angle` — removed in 4.1; use `shade_smooth_by_angle`.
- Don't stack 3+ materials on one prop, and don't ship a unique 2K texture on background clutter.
- Don't leave the origin at the world/volume center or forget `transform_apply` before export.
- Don't exceed the vert caps without LODs — anything over budget with no LOD chain gets flagged.

See also: `blockout`, `hard_surface`, `uv_workflow`, `materials_shading`, `texture_bake`, `lod_collision`, `asset_qa`, `uefn_export`.
