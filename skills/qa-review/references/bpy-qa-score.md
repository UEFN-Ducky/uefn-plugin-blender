---
description: "One-call asset QA score in bpy: non-manifold, zero-area, doubles, n-gons, inward normals, z-fighting, floating, UV overlap, influences, negative or unapplied scale, .001 names, tri and material budgets per profile (UEFN, Unreal, Roblox, render, print); 100 minus 10 per error, 3 per warning"
metadata:
  label: "QA Score Script"
---

# QA Score Script

Run last, before export. `pass` = no errors. Score = 100 - 10 per error - 3 per warning.

| Profile | Tri cap per mesh | Max influences | Notes |
|---|---|---|---|
| uefn | 20,000 | 4 | pivot at base centre, z=0 |
| ue5 | none | 8 | |
| roblox | 20,000 tris, 10,000 verts | 4 | n-gons are errors |
| render | none | - | skip pivot, UV, ground |
| print | none | - | open edges are errors |

| Budget | Tris | Materials |
|---|---|---|
| prop | 3k | 2 |
| module | 5k | 1 |
| mobile | 10k | 2 |
| weapon | 15k | 3 |
| vehicle | 50k | 5 |
| char | 60k | 8 |
| hero | 100k | 5 |

```python
import bpy, bmesh, re

def qa(objs, profile="uefn", budget=None, eps=0.001, tol=0.002):  # metres
    cap, cap_v, limit, ngon_err = {"uefn": (20000, 0, 4, False), "ue5": (0, 0, 8, False),
        "roblox": (20000, 10000, 4, True), "render": (0, 0, 0, False), "print": (0, 0, 0, False)}[profile]
    issues, tris, mats, low = [], 0, set(), 1e9
    dg = bpy.context.evaluated_depsgraph_get()
    centres = {}
    for o in objs:
        me = o.evaluated_get(dg).to_mesh()
        bm = bmesh.new(); bm.from_mesh(me); bm.transform(o.matrix_world); bm.normal_update()
        t = sum(len(f.verts) - 2 for f in bm.faces); tris += t
        mats.update(s.material.name for s in o.material_slots if s.material)
        low = min(low, min(v.co.z for v in bm.verts))
        open_e = sum(e.is_boundary for e in bm.edges)
        nm = sum(not e.is_manifold and not e.is_boundary for e in bm.edges)
        if nm: issues.append(("error", f"{o.name} {nm} non-manifold edges"))
        if open_e: issues.append(("error" if profile == "print" else "warn", f"{o.name} {open_e} open edges"))
        zero = sum(f.calc_area() < 1e-8 for f in bm.faces)
        if zero: issues.append(("error", f"{o.name} {zero} zero-area faces"))
        doubles = len(bmesh.ops.find_doubles(bm, verts=bm.verts, dist=0.0005)["targetmap"])
        if doubles: issues.append(("warn", f"{o.name} {doubles} doubles"))
        ngons = sum(len(f.verts) > 4 for f in bm.faces)
        if ngons: issues.append(("error" if ngon_err else "warn", f"{o.name} {ngons} n-gons"))
        if not open_e and not nm and bm.calc_volume(signed=True) < 0:
            issues.append(("error", f"{o.name} normals point inward"))
        for f in bm.faces:  # z-fighting: same centre, parallel normals
            key = tuple(round(c / eps) for c in f.calc_center_median())
            if any(abs(f.normal.dot(n)) > 0.99 for n in centres.get(key, ())):
                issues.append(("error", f"{o.name} z-fighting faces")); break
            centres.setdefault(key, []).append(f.normal.copy())
        if cap and t > cap: issues.append(("error", f"{o.name} {t} tris > {cap}"))
        if cap_v and len(bm.verts) > cap_v: issues.append(("error", f"{o.name} {len(bm.verts)} verts > {cap_v}"))
        if limit and o.vertex_groups:
            many = sum(sum(g.weight > 1e-4 for g in v.groups) > limit for v in o.data.vertices)
            if many: issues.append(("warn", f"{o.name} {many} verts > {limit} influences"))
        s = o.matrix_world.to_scale()
        if s.x * s.y * s.z < 0: issues.append(("error", f"{o.name} negative scale"))
        elif max(abs(c - 1) for c in o.scale) > 1e-3: issues.append(("warn", f"{o.name} scale not applied"))
        if re.search(r"\.\d{3}$", o.name): issues.append(("warn", f"{o.name} duplicate-style name"))
        if not me.uv_layers: issues.append(("warn", f"{o.name} no UVs"))
        bm.free(); o.evaluated_get(dg).to_mesh_clear()
    if profile not in ("render", "print") and low > tol: issues.append(("warn", f"floats {low * 100:.1f} cm"))
    if budget:
        bt, bm_ = {"prop": (3000, 2), "module": (5000, 1), "mobile": (10000, 2), "weapon": (15000, 3),
                   "vehicle": (50000, 5), "char": (60000, 8), "hero": (100000, 5)}[budget]
        if tris > bt: issues.append(("error", f"{tris} tris > {budget} {bt}"))
        if len(mats) > bm_: issues.append(("warn", f"{len(mats)} materials > {bm_}"))
    errors = sum(s == "error" for s, _ in issues)
    return {"score": max(0, 100 - 10 * errors - 3 * (len(issues) - errors)), "pass": errors == 0,
            "tris": tris, "issues": [m for _, m in issues]}

print(qa([o for o in bpy.context.selected_objects if o.type == "MESH"], "uefn", "prop"))
```

## Safe fixes (then run `qa` again)

| Issue | Fix |
|---|---|
| doubles | `bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)` |
| zero-area | `bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=0.0001)` |
| inward normals | `bmesh.ops.recalc_face_normals(bm, faces=bm.faces)` |
| n-gons | `bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])` |
| scale | `bpy.ops.object.transform_apply(scale=True)` |
| pivot | cursor to (bbox centre x, y, min z), `origin_set(type="ORIGIN_CURSOR")`, then move the object to z=0 |
| .001 | `o.name = re.sub(r"\.\d{3}$", "", o.name)` |

UV overlap matters only under a unique (baked) texture: check it in `uv-workflow`. Not auto-fixable: z-fighting, floating, budgets (`lod-pipeline`, `asset-optimization`).

Adapted from Blender Agent Skills by EL4CTEO (asset-qa; MIT), majidmanzarpour/blender-game-skills (validate, tri budgets; MIT) and HoldMyBeer-gg/blenderwright (mesh quality; MIT). Same checks as Forge `qa`.
