# Hard surface

Sci-fi hulls, weapons, armor, industrial props, mech parts — anything with machined edges. Load for boolean/bevel modeling, panel lines, greebles, and hard-surface shading setup. All snippets run via `blender_execute_blender_code` on Blender 4.5 LTS. Work in meters, real-world sizes.

## Strategy 2026 — pick the shading path first

| Asset type | Path | Why |
|---|---|---|
| Angular armor, weapons, kit pieces, vehicles | **Mid-poly**: real bevels + weighted normals | Game default. No bake needed for edges; normal map demoted to micro-detail |
| Smooth curved shells (sleek helmet, car body) | Sub-D high poly → low poly + bake | Only path that holds continuous curvature; see `texture_bake` |
| Micro detail (grip knurling, tiny vents) | Trim sheet / normal map only | Never model what a texel can carry; see `materials_shading` |

Mid-poly means: chamfer every visible edge with a real 1-segment bevel, bend vertex normals toward the big flat faces (weighted normals) so the shading transition lives entirely on the bevel, skip support loops. It is the dominant game workflow — cheaper than sub-D, bake-optional, and UEFN's budgets (simple prop LOD0 400–2,500 tris, complex up to 9,000 by size class) fit it well. See `lod_collision` for the full budget table.

## Boolean + bevel workflow

Blockout first (`blockout`), then cut. Save a checkpoint before every destructive apply: `bpy.ops.wm.save_mainfile()`.

```python
import bpy
ob = bpy.data.objects["SM_Hull"]
cutter = bpy.data.objects["Cutter_Vent"]      # keep cutters in COL_Cutters
cutter.display_type = 'WIRE'; cutter.hide_render = True

mod = ob.modifiers.new("Bool_Vent", 'BOOLEAN')
mod.object = cutter
mod.operation = 'DIFFERENCE'                  # 'UNION' / 'INTERSECT'
mod.solver = 'EXACT'   # 5.0: the fast solver enum renamed 'FAST' -> 'FLOAT'; 'EXACT' unchanged
with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob]):
    bpy.ops.object.modifier_apply(modifier=mod.name)
```

Keep booleans live (don't apply) while iterating; apply only when the shape is locked, then run cleanup. `mod.operand_type = 'COLLECTION'` + `mod.collection` cuts with a whole cutter collection at once.

### Cleanup after apply

Booleans leave doubled verts, slivers, and messy coplanar splits. Clean with bmesh (no mode juggling):

```python
import bmesh, math
me = ob.data
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
bmesh.ops.dissolve_degenerate(bm, dist=0.0005, edges=bm.edges)
bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(1.0),
                         verts=bm.verts[:], edges=bm.edges[:], delimit={'SHARP'})
bm.to_mesh(me); bm.free(); me.update()
```

Limited dissolve produces n-gons — fine on planar faces of a static mesh (the exporter triangulates), bad on anything curved. Quads matter far less here than in `face_topology`; planarity is what matters. Deeper repair: `mesh_cleanup`.

### Bevel pass

Tag edges by angle into the `bevel_weight_edge` attribute, then one WEIGHT-limited Bevel modifier:

```python
import bmesh, math
me = ob.data
bm = bmesh.new(); bm.from_mesh(me)
weights = [0.0] * len(me.edges)
for e in bm.edges:
    if len(e.link_faces) == 2 and e.calc_face_angle() > math.radians(30):
        weights[e.index] = 1.0
bm.free()
attr = me.attributes.get("bevel_weight_edge") or me.attributes.new("bevel_weight_edge", 'FLOAT', 'EDGE')
attr.data.foreach_set("value", weights)
me.update()

bev = ob.modifiers.new("Bevel", 'BEVEL')
bev.limit_method = 'WEIGHT'
bev.width = 0.004            # meters; see width tiers below
bev.segments = 1             # mid-poly chamfer; 2-3 for hero close-ups
bev.miter_outer = 'MITER_ARC'
bev.use_clamp_overlap = True
```

Hand-edit weights (0.0–1.0 scales width per edge) for a two-tier look from a single modifier.

## Shading: Smooth by Angle + weighted normals

`mesh.use_auto_smooth` is gone (removed 4.1). The modern stack:

```python
import bpy, math
ob = bpy.data.objects["SM_Hull"]
with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob]):
    # Writes smooth shading + the boolean edge attribute 'sharp_edge'. No modifier added.
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(45), keep_sharp_edges=False)

wn = ob.modifiers.new("WeightedNormal", 'WEIGHTED_NORMAL')
wn.mode = 'FACE_AREA'        # big faces win the normal — flat planes stay flat
wn.keep_sharp = True         # respects sharp_edge marks
wn.weight = 50
```

- Order: Boolean → Bevel → WeightedNormal **last** in the stack, always.
- Alternative A: `bpy.ops.object.shade_auto_smooth(angle=...)` adds the live "Smooth by Angle" node-group modifier instead of baking the attribute — use while the mesh is still changing, since new edges re-evaluate each frame.
- Alternative B: `bev.harden_normals = True` on the Bevel modifier does a lighter version of the same job (requires smooth shading). Pick harden_normals **or** a WeightedNormal modifier, never both — they fight.

## Avoiding shading artifacts: bevel width vs mesh density

- **Bevel wider than its smallest neighboring face** = overlap spikes. `use_clamp_overlap=True` hides it but makes widths inconsistent; the real fix is merging tiny faces (limited dissolve) or narrowing that edge's weight.
- **Gradient blotches on flat panels** = normals still averaged. Confirm WeightedNormal is last, `mode='FACE_AREA'`, and the blotchy face isn't split into slivers (dissolve them).
- **Black/inverted shading after booleans** = flipped normals. `bmesh.ops.recalc_face_normals(bm, faces=bm.faces)` or select-all + `bpy.ops.mesh.normals_make_consistent(inside=False)` in edit mode.
- **Pinching at 3-way bevel corners** = use `miter_outer='MITER_ARC'` and keep the three incoming widths equal.
- **Width tiers**: pick 2–3 sizes per asset and stick to them — e.g. on a ~1 m prop: 8 mm structural silhouette edges, 3–4 mm secondary panels, 1.5 mm details. Uniform edge width is what makes an asset read "manufactured".

## Panel lines, bolts, greebles

Panel lines: thin box "blades" (2–4 mm thick, slightly protruding) as DIFFERENCE cutters cut a groove that catches AO and bakes cleanly. Array the blade for repeated seams. Purely visual seams on flat areas are cheaper as trim-sheet texture — see `materials_shading`.

### Arrays for repeated details

```python
import bpy
bolt = bpy.data.objects["SM_Bolt"]
row = bolt.copy(); row.data = bolt.data       # linked duplicate, shared mesh
bpy.context.scene.collection.objects.link(row)
arr = row.modifiers.new("Array", 'ARRAY')
arr.count = 8
arr.use_relative_offset = False
arr.use_constant_offset = True
arr.constant_offset_displace = (0.12, 0.0, 0.0)   # meters along local X
```

Stack a second Array on Y for grids; add a Curve modifier to run bolts along a rim.

### Geometry-nodes greeble scatter

Scatter kit chips over hull faces non-destructively (see `geometry_nodes` for fundamentals):

```python
import bpy
ob = bpy.data.objects["SM_Hull"]
gt = bpy.data.node_groups.new("GN_Greeble", 'GeometryNodeTree')
gt.interface.new_socket(name="Geometry", in_out='INPUT',  socket_type='NodeSocketGeometry')
gt.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
n_in, n_out = gt.nodes.new('NodeGroupInput'), gt.nodes.new('NodeGroupOutput')
dist = gt.nodes.new('GeometryNodeDistributePointsOnFaces')
dist.distribute_method = 'POISSON'
dist.inputs["Distance Min"].default_value = 0.08
dist.inputs["Density Max"].default_value = 200.0
info = gt.nodes.new('GeometryNodeObjectInfo')
info.inputs["Object"].default_value = bpy.data.objects["Kit_Chip"]
info.inputs["As Instance"].default_value = True
inst = gt.nodes.new('GeometryNodeInstanceOnPoints')
join = gt.nodes.new('GeometryNodeJoinGeometry')
real = gt.nodes.new('GeometryNodeRealizeInstances')   # exporters need real geometry
L = gt.links
L.new(n_in.outputs["Geometry"], dist.inputs["Mesh"])
L.new(dist.outputs["Points"],   inst.inputs["Points"])
L.new(dist.outputs["Rotation"], inst.inputs["Rotation"])   # align chips to surface
L.new(info.outputs["Geometry"], inst.inputs["Instance"])
L.new(inst.outputs["Instances"], join.inputs["Geometry"])
L.new(n_in.outputs["Geometry"],  join.inputs["Geometry"])
L.new(join.outputs["Geometry"],  real.inputs["Geometry"])
L.new(real.outputs["Geometry"],  n_out.inputs["Geometry"])
mod = ob.modifiers.new("Greeble", 'NODES'); mod.node_group = gt
```

Confine scatter to tagged zones by wiring a Named Attribute node into `dist.inputs["Selection"]`. Watch the tri count — greebles blow UEFN budgets fast; keep chips under ~100 tris each.

## Scriptable kitbash assembly

Build a `COL_Kit` collection of finished parts once, then assemble variants by script with linked duplicates (shared mesh data = near-free memory):

```python
import bpy, math
kit = bpy.data.collections["COL_Kit"]
asm = bpy.data.collections.get("COL_Assembly") or bpy.data.collections.new("COL_Assembly")
if asm.name not in bpy.context.scene.collection.children:
    bpy.context.scene.collection.children.link(asm)

def place(part, loc, rot_z=0.0, scale=1.0):
    ob = kit.objects[part].copy()             # .data stays shared
    ob.location = loc
    ob.rotation_euler = (0.0, 0.0, math.radians(rot_z))
    ob.scale = (scale,) * 3
    asm.objects.link(ob)
    return ob

place("Kit_Thruster", (0.0, -1.2, 0.4))
place("Kit_Thruster", (0.0,  1.2, 0.4), rot_z=180)
place("Kit_AntennaMast", (0.6, 0.0, 1.1), scale=0.75)
```

Join into one export mesh only at the end (join makes data single-user, breaking the sharing):

```python
parts = [o for o in asm.objects if o.type == 'MESH']
with bpy.context.temp_override(active_object=parts[0], selected_objects=parts,
                               selected_editable_objects=parts):
    bpy.ops.object.join()
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
```

Non-uniform scale on kit parts skews bevel widths after apply — prefer scale 1.0 parts and size variety in the kit itself. Naming (`SM_`, `COL_`): `scene_organization`.

## Edge-wear-ready bevels (baking)

Edge-wear generators (curvature-driven masks in Substance/etc.) only see edges that exist in the baked normal/curvature map:

- A bevel must span **at least ~2 texels** at bake resolution. At 2K over a 1 m asset, 1 texel ≈ 0.5 mm → keep wear-target bevels ≥ 1 mm wide. Sub-texel bevels vanish from the curvature map and get zero wear.
- Mid-poly assets can bake curvature/AO **from themselves** (no separate high poly) — the real bevels are the source. Use 2 segments on edges that should wear as a rounded lip; 1-segment chamfers read as machined and take a harder wear line.
- Keep widths in your 2–3 tiers: wear width then stays consistent across the asset, which is most of what makes wear look intentional. Bake recipes: `texture_bake`; UVs first: `uv_workflow`.

## Sub-D: only when needed

Reserve Subdivision Surface for continuously curved shells that will be baked down. Hold edges with the `crease_edge` float edge attribute (the 4.x home of edge creases) or support loops; never export a live level-2+ sub-D on an angular asset — it multiplies tris for zero silhouette gain. `modifiers` covers stack patterns; `texture_bake` covers the high→low bake.

## Version notes

- 4.1 removed mesh-level auto smooth — everything here already uses `shade_smooth_by_angle` / Smooth by Angle + `sharp_edge`.
- 5.0 renames the boolean fast solver enum `'FAST'` → `'FLOAT'` (`'EXACT'`, used above, is unchanged).
- 5.0 ships new geometry-nodes-based built-in modifiers (Array, Scatter on Surface) — the classic `'ARRAY'` recipe above targets 4.2–4.5.

## Verify

- `blender_get_viewport_screenshot` from 3/4-front, side, and rear: silhouette reads at gameplay distance; flat panels show no gradient blotches; bevel highlights are a consistent width.
- After each boolean apply: screenshot the cut region — no pinching, no missing faces, cutters no longer visible.
- Budget check: `me = ob.data; me.calc_loop_triangles(); print(len(me.loop_triangles))` against the UEFN caps in `lod_collision`; `blender_get_object_info` to confirm scale is 1.0.
- Stack check: WeightedNormal is the last modifier; `print(me.attributes.get("sharp_edge"))` is not None after the shading pass.

## Don'ts

- Don't touch `mesh.use_auto_smooth` / `auto_smooth_angle` — removed in 4.1; scripts using them throw immediately.
- Don't put WeightedNormal anywhere but last, and don't combine it with Bevel `harden_normals`.
- Don't apply booleans without a save checkpoint and a cleanup pass — doubled verts poison every later bevel.
- Don't export live cutters or greeble source chips: keep them in `COL_Cutters` / `COL_Kit` and exclude those collections at export (`uefn_export`).
- Don't build angular armor with sub-D + support loops — mid-poly is cheaper and bakes are optional.
- Don't bevel at one uniform width everywhere, and don't ship sub-texel bevels expecting edge wear to find them.
- Don't leave non-planar n-gons after limited dissolve — they triangulate unpredictably at export.

See also: `blockout`, `modifiers`, `mesh_cleanup`, `geometry_nodes`, `uv_workflow`, `texture_bake`, `materials_shading`, `lod_collision`, `uefn_export`, `verify_loop`.
