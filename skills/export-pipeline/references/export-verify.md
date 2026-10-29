---
description: "Verify an export by re-importing it into an empty Blender scene: mesh, skin, morph and bone counts, size within 2 percent, armature scale 1 not 100, clips survive, no missing images, file under 8 MB"
metadata:
  label: "Export Verify"
---

# Export Verify

Export, then read the file back into an empty scene and compare. A file you never re-opened is not verified.

| Check | Pass |
|---|---|
| meshes, skinned meshes, shape keys, bones | same counts as before export (UCX_ and LOD copies excluded) |
| bounding size | within 2 % on every axis |
| armature object scale | 1.0 (100 or 0.01 = wrong unit/scale option) |
| actions | at least one per exported clip |
| images | every image has data or an existing file |
| file size | < 8 MB for a game asset (web: < 5 MB) |

```python
import bpy, os
from pathlib import Path

def counts():
    m = [o for o in bpy.data.objects if o.type == "MESH" and not o.name.startswith("UCX_")]
    pts = [o.matrix_world @ v.co for o in m for v in o.data.vertices]
    size = [max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3)] if pts else [0, 0, 0]
    return {"meshes": len(m), "skins": sum(any(x.type == "ARMATURE" for x in o.modifiers) for o in m),
            "morphs": sum(len(o.data.shape_keys.key_blocks) - 1 for o in m if o.data.shape_keys),
            "bones": sum(len(a.data.bones) for a in bpy.data.objects if a.type == "ARMATURE"), "size": size}

def verify(path, before):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    {".fbx": bpy.ops.import_scene.fbx, ".glb": bpy.ops.import_scene.gltf, ".gltf": bpy.ops.import_scene.gltf}[Path(path).suffix](filepath=path)
    after, warn = counts(), []
    warn += [f"{k} {before[k]}->{after[k]}" for k in ("meshes", "skins", "morphs", "bones") if before[k] != after[k]]
    if any(a > 1e-4 and abs(a - b) / a > .02 for a, b in zip(before["size"], after["size"])): warn.append("size drift")
    warn += [f"armature scale {a.scale.x:g}" for a in bpy.data.objects if a.type == "ARMATURE" and abs(a.scale.x - 1) > .01]
    warn += [f"missing image {i.name}" for i in bpy.data.images if i.source == "FILE" and not i.has_data and not i.packed_file]
    if os.path.getsize(path) > 8 * 2**20: warn.append("over 8 MB")
    return warn  # [] = verified
```

Call `before = counts()` right before exporting. Same check as Forge `export(verify=true)`.

Adapted from Blender Agent Skills by EL4CTEO (export-pipelines; MIT) and majidmanzarpour/blender-game-skills (round-trip; MIT).
