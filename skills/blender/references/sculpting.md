# Sculpting

Organic massing and high-frequency detail before retopo. Sculpt is **not** the export mesh. Prefer large form brushes first; detail only after proportions lock (`blockout`). Via `blender_execute_blender_code` where scriptable — many brush strokes are interactive; use code for remesh, multires levels, and checkpoints.

## When

- Soft volumes / creatures before `retopology`
- High-frequency detail to bake (`texture_bake`)
- Not for mid-poly hard surface (use `hard_surface` bevels instead)

## Dynotopo vs Multires

| Mode | Use |
|---|---|
| **Dyntopo** | Early exploration, changing topology freely |
| **Multires** | Locked topology, subdivided levels, bake-friendly |
| Both blindly | Avoid — pick one phase |

```python
import bpy
ob = bpy.data.objects["SM_Sculpt"]
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
bpy.ops.object.mode_set(mode='SCULPT')

# Multires path
mod = ob.modifiers.get("Multires") or ob.modifiers.new("Multires", 'MULTIRES')
# Subdivide levels in UI or:
# bpy.ops.object.multires_subdivide(modifier="Multires")
```

Remesh for even density (voxel):

```python
import bpy
ob = bpy.data.objects["SM_Sculpt"]
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
bpy.ops.object.mode_set(mode='OBJECT')
ob.data.remesh_voxel_size = 0.01   # meters; smaller = denser
bpy.ops.object.voxel_remesh()
```

Save before remesh: `bpy.ops.wm.save_mainfile()`.

## Scriptable vs manual

**Code OK:** enter sculpt mode, remesh, add Multires, set voxel size, hide/show, screenshot verify, apply modifiers when done.

**Also scriptable — load `sculpt_brushes`:** real brush strokes (Smooth, Crease Sharp, Clay, Grab…) via synthesized `bpy.ops.sculpt.brush_stroke` stroke points, per-vertex `.sculpt_mask` writing, and `sculpt.mesh_filter` (SURFACE_SMOOTH etc.) for deterministic brush-quality smoothing. That subskill has the viewport-framing setup, brush activation (4.3+ Essentials assets), and a smooth-face recipe.

**Still manual / user-guided:** freehand artistic detailing, pose brush finesse, anything needing real-time pen pressure feel. Prefer: blockout in Object/Edit → scripted sculpt passes (`sculpt_brushes`) or short user-guided bursts → remesh → continue → retopo.

## Pipeline

```
blockout → sculpt massing → (detail) → remesh/cleanup → retopology → uv → bake → game mesh
```

Verify silhouette with `blender_get_viewport_screenshot` + Flat shading (`verify_loop`). Fix proportions in blockout, not with 50 micro brushes.

## Export rule

Never ship Multires level 5 / dyntopo soup to UEFN. Always:

1. Retopo to game density, **or**
2. Bake high→low normals onto a proper low (`texture_bake`).

## Don'ts

- Don't sculpt over bad proportions — fix `blockout` first.
- Don't mix live Cloth + Multires without a plan.
- Don't forget to apply/remove sculpt-only modifiers before export.

Next: `retopology` → `uv_workflow` → `texture_bake`.
