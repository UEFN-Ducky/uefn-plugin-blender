# Scale library

Real-world sizes in **meters** (Blender scene units). UEFN uses **cm** (1 uu = 1 cm)
— expect ×100 on import unless FBX baked scale. Wrong scale is the silent #1 failure.

Load before `blockout`. Via `blender_execute_blender_code`.

## Scene setup

```python
import bpy
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0   # 1 Blender unit = 1 meter
```

Place a **1.8 m** empty or thin cube as human reference; never model "eyeball hero"
without a scale neighbor.

## Humans & openings

| Thing | Size (m) |
|-------|----------|
| Adult height | 1.7–1.9 (use **1.8**) |
| Eye height | ~1.6–1.7 |
| Shoulder width | ~0.4–0.5 |
| Door (clear) | **2.1 H × 0.9 W** |
| Interior corridor | ≥ 1.2 W (combat lanes wider) |
| Stair riser / tread | ~0.18 / 0.28 |

Fortnite feel: leveldesign uses 512 uu cells (~5.12 m) and ~190 uu player —
props that ignore human scale look like toys or monuments.

## Props

| Thing | Size (m) |
|-------|----------|
| Crate / loot box | 0.4–0.6 |
| Barrel | ~0.9 H × 0.6 Ø |
| Chair seat height | ~0.45 |
| Table | ~0.75 H |
| Lantern / device | 0.2–0.4 |
| Weapon (rifle length) | 0.8–1.2 |
| Pistol | ~0.2 |
| Sword | 0.9–1.2 |

## Vehicles & env

| Thing | Size (m) |
|-------|----------|
| Car length / width / height | ~4.5 / 1.8 / 1.5 |
| Truck length | 6–12 |
| Wall module | 2 / 4 / 8 (pick a kit grid) |
| Story height | ~3.0–3.5 (Fort-ish story ~3.84 m = 384 uu) |
| Tree (game) | 4–12 H; cards, not botanical leaf counts |

## Quick verify

```python
import bpy
ob = bpy.data.objects["SM_Prop"]
# Axis-aligned size in meters (object scale applied)
import mathutils
bbox = [mathutils.Vector(c) for c in ob.bound_box]
size = ob.matrix_world.to_scale()  # prefer dimensions:
print(ob.name, "dimensions_m", tuple(ob.dimensions))
```

Screenshot next to the 1.8 m reference (`verify_loop`).

## Don'ts

- Don't mix cm-authored imports with meter scenes without converting.
- Don't blockout a "door" at 0.3 m because the cube default looked fine.
- Don't export to UEFN without checking bounds after import (`fbx_import_pipeline` in modeling pack).

Next: `blockout` → discipline skill → `asset_qa`.
