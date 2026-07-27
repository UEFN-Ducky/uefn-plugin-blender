# Trim sheets

Shared atlas / trim UVs for modular env and hard-surface — few materials, high
reuse. Load with `environments_modular`, `hard_surface`, `uv_workflow`. Via
`blender_execute_blender_code`.

## When

- Walls, floors, trims, pipes, panels that tile
- Sci-fi kits with repeated rivets / slots / edges
- Not for unique hero faces (those get unique UVs)

## Idea

One (or few) **trim sheet** textures: borders, bolts, grills, wear strips packed
in UV space. Many meshes sample **different regions** of the same sheet —
texel density stays consistent; material count stays low.

```
T_Trim_Metal_BC / _N / _ORM
MAT_Trim_Metal  → used by SM_Wall_A, SM_Trim_Cap, SM_Floor_Edge…
```

## Workflow

1. Define module grid (`environments_modular`) and texel density target (`uv_workflow`).
2. Author or reuse a trim atlas (Blender paint / external / bake from high).
3. Unwrap strips to the matching atlas cells — **straight UVs** on pipes/beams.
4. Overlapping UVs **OK** for identical trim instances; bad for unique wear you care about.
5. One `MAT_` / UEFN `MI_` for the sheet (`materials_shading` → materials pack handoff).

```python
import bpy
# Example: assign same material to kit pieces
mat = bpy.data.materials.get("MAT_Trim_Metal")
for name in ("SM_Wall_A", "SM_Trim_Cap", "SM_Floor_Edge"):
    ob = bpy.data.objects.get(name)
    if not ob:
        continue
    if ob.data.materials:
        ob.data.materials[0] = mat
    else:
        ob.data.materials.append(mat)
```

## UV tips

- Keep trim strips axis-aligned in UV for less filtering shimmer.
- Padding between atlas cells for mips (`uv_workflow` margins).
- Second UV for lightmaps when unique lighting needs it — trim sheet stays on UV0.

## Mid-poly + trim

Model chamfers in geo (`hard_surface`); put micro detail (screws, seams) in the
normal/ORM trim — don't boolean every rivet.

## Don'ts

- Don't unique-unwrap every modular wall to a dedicated 2K.
- Don't mix wildly different texel densities across one kit.
- Don't put a character face on a trim sheet.

Next: `uv_workflow` → `materials_shading` → `asset_qa` → `uefn_export`.
