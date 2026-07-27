# Hair groom

Game path for UEFN: **hair cards** (alpha strips) or short shell layers — not millions of curve strands. Curves / particle hair are for lookdev and card generation. Via `blender_execute_blender_code`.

## Game preferred

| Technique | Use |
|---|---|
| Hair cards | Long hair, hero characters — atlas + alpha |
| Shell / fin layers | Short hair, fur, peach fuzz |
| Curve hair export | Avoid for UEFN runtime |

## Cards workflow

1. Cap / scalp mesh under hair (no bald holes).
2. Place strip planes along flow; UV to atlas.
3. Alpha in material (`materials_shading`); double-sided or two-sided cards.
4. Origin / skinning: cards parented/skinned to head bones (`skinning_weights`).

```python
import bpy
# Simple card plane
bpy.ops.mesh.primitive_plane_add(size=0.05, location=(0, 0, 1.7))
card = bpy.context.active_object
card.name = "SM_HairCard_01"
# Rotate to follow hair direction; duplicate along scalp
```

Atlas tips: pack cards in one texture; consistent texel density with face (`uv_workflow`). Keep card count reasonable (tens–low hundreds for hero, not thousands).

## Curves hair (lookdev → bake)

```python
import bpy
# Blender 3.3+ curves hair objects — generate in UI / add curves
# For export: convert to mesh cards or bake textures; do not ship raw curves
ob = bpy.data.objects.get("Hair")
if ob and ob.type == 'CURVES':
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    # Convert to mesh for card extraction / bake proxy
    bpy.ops.object.convert(target='MESH')
```

Bake hair lighting into textures when possible; simplify for LOD1+.

## Verify

- Silhouette side / back / 3/4 (`verify_loop` screenshots).
- Cap coverage under part lines.
- Cards don't explode normals (apply scale; consistent facing).

## Don'ts

- Don't export particle/curve hair counts to UEFN.
- Don't skip scalp cap.
- Don't unique-texture every card — use an atlas.

Next: `materials_shading` → `skinning_weights` (if character) → `skeletal_export` or `uefn_export`.
