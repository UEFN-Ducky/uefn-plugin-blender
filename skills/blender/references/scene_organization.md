# Scene organization

Load this when starting a new .blend for UEFN work, restructuring a messy scene, or preparing collections for export. Everything runs through `blender_execute_blender_code`; confirm structure with `blender_get_scene_info`.

## Naming conventions

| Data | Pattern | Example |
|---|---|---|
| Collection | `COL_` | `COL_SM_Crate_A` |
| Static mesh object + its mesh data | `SM_` | `SM_Crate_A` |
| Skeletal mesh object | `SK_` | `SK_Guard` |
| Material | `MAT_` (alt `M_`) | `MAT_Crate_Wood` |
| Collision shells | `UCX_<meshname>_##` (also `UBX_`/`USP_`/`UCP_`, see `lod_collision`) | `UCX_SM_Crate_A_00` |
| Lights / cameras (never exported) | `LGT_` / `CAM_` | `LGT_Key` |
| Mirrored bones / vertex groups / shape keys | `.L` / `.R` suffix | `hand.L` |

Rules:

- Object name and mesh datablock name must match — exports and debugging stay sane.
- `.L` / `.R` go at the *end* of the name. Blender's Symmetrize, X-mirror posing, and weight mirroring key off this suffix (`rigging_armatures`, `skinning_weights` depend on it).
- ASCII, underscores instead of spaces. Keep names short: 4.x truncates ID names at 63 bytes. `# 5.0: limit raised to 255 bytes — still stay short for the 4.2→5.0 window.`

Batch rename pass (run early, before anything references names):

```python
import bpy, re

PREFIX_OK = re.compile(r"^(SM|SK|UCX|UBX|USP|UCP|LGT|CAM)_")

for ob in bpy.data.objects:
    if ob.type == 'MESH':
        if not PREFIX_OK.match(ob.name):
            ob.name = "SM_" + ob.name.replace(" ", "_")
        ob.data.name = ob.name          # keep datablock in sync

for mat in bpy.data.materials:
    if not mat.name.startswith(("MAT_", "M_")):
        mat.name = "MAT_" + mat.name.replace(" ", "_")
```

## Units and scale — first action in any new file

```python
scn = bpy.context.scene
scn.unit_settings.system = 'METRIC'
scn.unit_settings.scale_length = 1.0    # 1 BU = 1 m; the export recipes handle m -> cm (UEFN: 1 uu = 1 cm)
scn.unit_settings.length_unit = 'METERS'
```

Model at real-world size against these references: UEFN character ≈ 1.9 m tall, door ≈ 2.1 m, one building tile = 512 uu = 5.12 m. Object scale must end up `(1, 1, 1)` before export — `bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)`; full checklist in `asset_qa`.

## Collection structure for a UEFN project

```
Scene Collection
├─ COL_SM_Crate_A        ← export unit: exactly one static asset
│    SM_Crate_A, UCX_SM_Crate_A_00, UCX_SM_Crate_A_01
├─ COL_SK_Guard          ← export unit: one armature + its meshes
├─ COL_WIP               ← blockouts, experiments — never exported
├─ COL_CUTTERS           ← boolean cutters, excluded from view layer
└─ COL_REF               ← reference images/meshes, excluded
```

Create the skeleton idempotently:

```python
import bpy

def ensure_collection(name, parent=None):
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    parent = parent or bpy.context.scene.collection
    if col.name not in parent.children:
        parent.children.link(col)
    return col

for name in ("COL_WIP", "COL_CUTTERS", "COL_REF"):
    ensure_collection(name)
ensure_collection("COL_SM_Crate_A").color_tag = 'COLOR_04'   # optional outliner color
```

Keep `COL_REF` / `COL_CUTTERS` out of the view layer so "visible objects" exports can never pick them up. `layer_collection.exclude` removes them from the view layer entirely; `collection.hide_viewport` is only a global disable toggle.

```python
def find_layer_collection(root, name):
    if root.collection.name == name:
        return root
    for child in root.children:
        hit = find_layer_collection(child, name)
        if hit:
            return hit

for name in ("COL_REF", "COL_CUTTERS"):
    lc = find_layer_collection(bpy.context.view_layer.layer_collection, name)
    if lc:
        lc.exclude = True
```

## Moving objects between collections

An object can sit in several collections at once; for export hygiene it should sit in exactly one. Unlink everywhere, then link once:

```python
def move_to_collection(ob, col):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    col.objects.link(ob)

crate = ensure_collection("COL_SM_Crate_A")
for ob in bpy.data.objects:
    if ob.name.startswith(("SM_Crate_A", "UCX_SM_Crate_A")):
        move_to_collection(ob, crate)
```

## One asset per export collection

The export hubs (`uefn_export`, `skeletal_export`) treat a collection as the export unit — the collection name minus `COL_` is the asset name. Enforce:

- Exactly one deliverable per `COL_SM_*` / `COL_SK_*` collection.
- The mesh's own `UCX_*` shells and LOD meshes (`lod_collision`) live *with* it in the same collection — nothing else. No lights, cutters, refs, or stray empties.
- Skeletal collections: one armature plus the meshes it deforms, nothing more.

When an exporter operates on the "active collection", set it explicitly:

```python
lc = find_layer_collection(bpy.context.view_layer.layer_collection, "COL_SM_Crate_A")
bpy.context.view_layer.active_layer_collection = lc
```

## Custom properties for pipeline metadata

Stamp pipeline facts on the object as ID properties — they survive .blend round-trips and can ride through export (FBX `use_custom_props=True`, glTF `extras`; wiring in `uefn_export`):

```python
ob = bpy.data.objects["SM_Crate_A"]
ob["uefn_asset"]  = "SM_Crate_A"
ob["export_path"] = "Props/Crates"
ob["texel_cm"]    = 10.24

ui = ob.id_properties_ui("texel_cm")
ui.update(min=0.0, soft_max=20.0, description="Target texels per cm")
```

Never start a property or attribute name with a dot — leading-dot names are Blender's hidden runtime namespace. `# 5.0: dict-style access to ADD-ON property groups (e.g. scene['cycles']) was removed; your own plain keys like ob["uefn_asset"] are unaffected.`

## Purging orphan data

Deleted objects leave zero-user meshes, materials, and images behind; they bloat the file and pollute `blender_get_scene_info` output. Checkpoint, then purge from `bpy.data` (no context needed, works headless):

```python
counts = lambda: {k: len(getattr(bpy.data, k))
                  for k in ("meshes", "materials", "images", "actions", "node_groups")}
before = counts()
bpy.ops.wm.save_mainfile()   # first save of a new file needs save_as_mainfile(filepath=...)
bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
print(before, "->", counts())
```

`do_recursive=True` clears whole chains (mesh → material → image) in one pass. Anything staged for later but currently unassigned must be pinned first: `mat.use_fake_user = True`.

## Version notes

- 5.0 raises the ID name length limit from 63 to 255 bytes; 4.2–4.5 silently truncate at 63.
- 5.0 writes compressed .blend files by default (`wm.save_mainfile` behavior change); no script change needed.
- Collection, view-layer, and ID-property APIs used here are stable across 4.2 LTS → 5.0.

## Verify

- `blender_get_scene_info`: every object lives in exactly one `COL_*` collection; zero default names (`Cube.001`, `Material`, bare `Collection`).
- Purge check: rerun the `counts()` snippet — datablock counts stay flat after a purge, and nothing you still need disappeared.
- `blender_get_viewport_screenshot` with `COL_REF`/`COL_CUTTERS` excluded: only deliverable geometry visible. Loop per `verify_loop`.
- Per export collection: one asset + its `UCX_*`/LOD meshes, object scale `(1,1,1)`.

## Don'ts

- Don't fix wrong sizes by touching `unit_settings.scale_length` — model in real meters at scale 1.0 and fix the geometry.
- Don't leave boolean cutters, reference meshes, lights, or cameras inside an export collection.
- Don't put two assets in one `COL_SM_*`/`COL_SK_*` collection — the exporters assume one asset per collection.
- Don't let object and mesh datablock names drift apart, and don't ship default names.
- Don't name custom properties or attributes with a leading dot.
- Don't purge orphans without a save checkpoint first — purge deletes *everything* with zero users, including work you staged but haven't assigned yet.
- Don't use `Scene Collection` as a dumping ground; unsorted work goes to `COL_WIP`.

See also: `bpy_fundamentals`, `uefn_export`, `skeletal_export`, `lod_collision`, `asset_qa`, `verify_loop`.
