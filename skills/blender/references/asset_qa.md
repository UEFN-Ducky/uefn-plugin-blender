# Asset QA

Gate before export. Fail any critical item → fix, don't ship. Pair with `blender_get_viewport_screenshot` and a runnable audit. Via `blender_execute_blender_code`.

## Checklist

- [ ] Applied scale / rotation (location optional)
- [ ] Named objects `SM_*` / `SK_*` + materials `MAT_*`
- [ ] Export collection only — no cutters / helpers / high-poly
- [ ] Manifold / clean normals (or known open edges intentional)
- [ ] UVs non-overlapping (hero) + padding; lightmap set if needed
- [ ] Polycount within budget (`lod_collision`)
- [ ] Pivot / origin sensible (ground contact for props/trees)
- [ ] Screenshots OK: front / side / 3/4 (`verify_loop`)
- [ ] `.blend` saved; textures saved to disk if baked
- [ ] Rigged: weights normalized, no crazy influences (`skinning_weights`)

## Runnable audit

```python
import bpy, bmesh

def audit(ob_name):
    ob = bpy.data.objects.get(ob_name)
    if ob is None or ob.type != 'MESH':
        return [f"MISSING {ob_name}"]
    issues = []
    if ob.scale != (1, 1, 1):
        issues.append("scale not applied")
    me = ob.data
    if not me.uv_layers:
        issues.append("no UVMap")
    bm = bmesh.new(); bm.from_mesh(me)
    bm.edges.ensure_lookup_table()
    nonman = [e for e in bm.edges if not e.is_manifold]
    if nonman:
        issues.append(f"non-manifold edges: {len(nonman)}")
    tris = sum(len(f.verts) == 3 for f in bm.faces)
    quads = sum(len(f.verts) == 4 for f in bm.faces)
    ngons = sum(len(f.verts) > 4 for f in bm.faces)
    issues.append(f"faces tris={tris} quads={quads} ngons={ngons} verts={len(bm.verts)}")
    bm.free()
    if not ob.data.materials:
        issues.append("no materials")
    return issues

print(audit("SM_Prop"))
```

## Purge before export

```python
import bpy
# Remove orphan meshes/materials after deleting helpers
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
```

## Don'ts

- Don't export from a dirty scene with `Cutter_*` visible.
- Don't skip screenshots on hero assets.
- Don't ship unsaved bake images.

Next: `uefn_export` or `skeletal_export`.
