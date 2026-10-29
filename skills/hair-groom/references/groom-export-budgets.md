---
description: "Shipping hair to engines: card and shell budgets per platform, UE groom Alembic export settings, fur shell counts, and the QA checks for cards (alpha overdraw, card count, atlas size)"
metadata:
  label: "Groom Export and Budgets"
---

# Groom Export and Budgets

| Target | Method | Budget |
|---|---|---|
| UEFN / mobile | hair cards on the head mesh | 3-8k tris, 1K-2K atlas, alpha-test (masked), no translucency |
| UE5 PC | Groom asset (Alembic curves) + cards LOD | 20-80k strands, cards at LOD1+ |
| Unity / Godot | hair cards | 5-15k tris, 2K atlas |
| Fur on creatures | shells | 4-8 shell layers, total <= 20k extra tris; or baked fur texture only |
| Roblox | hair cards / mesh accessory | <= 4k tris on the head accessory |

UE groom Alembic: select the Curves object, `bpy.ops.wm.alembic_export(filepath=p, selected=True, export_hair=True, uvs=True, curves_as_mesh=False, flatten=False)`, then in UE import as Groom with scale 1 (Blender metres) or 100 if exported in metres without unit conversion. Name groups `GRP_<Region>` (scalp, brows, lashes).

Card QA:
- Overdraw: no more than 3-4 stacked alpha cards on any pixel in a front `turntable-and-views` render.
- Cards root inside the scalp, tips fanned; normals point out (recalc), so lighting doesn't flip.
- Atlas: strips sorted by width, 8 px padding at 2K.
- Run `qa-review/references/bpy-qa-score.md` with the target profile: hair counts toward the character budget.

Adapted from Blender Agent Skills by EL4CTEO (hair; MIT) and arjun988/blender-skills (hair-groom; MIT).
