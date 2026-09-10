---
name: blender
description: "Control Blender 5.1+ via UEFN-Ducky and the official Blender Lab MCP add-on — model anything with bpy (hard surface, faces, characters, organic, props, env), rig/skin/animate, cloth & hair, UVs/materials/baking, scene analysis (polycount, material users, datablock renames), screenshot verify loops, import/export to UEFN"
license: MIT
metadata:
  label: Blender
  version: 8
  author: UEFN-Ducky
  copyright: Copyright 2026 Mindful Path Company, LLC
  allow_redistribute: true
  managed_by: uefn-ducky
  source_plugin_id: blender
---

# Blender — director (model in Blender via MCP)

You drive Blender **5.1+** through the **blender** Store plugin (`blender_*` on the shared `uefn-ducky` MCP), which ships the **official Blender Lab MCP add-on**. Ducky is the MCP server and the LLM client — never spawn `uvx blender-mcp` or a second Blender MCP server.

**Blender-only work does NOT need the UEFN editor.** If Blender is connected, proceed — do not wait for Fortnite.

**Path choice:** modeling can be Blender **or** UEFN. If unclear, ask once. Export-to-UEFN is a later step.

**SaaS generation:** Install Store plugin **meshy** (`meshy_*`) or **studio3d** (`studio3d_*`). Then import / clean / export here. Those plugins are **not** part of this one. Free Poly Haven / Sketchfab downloads: `urllib` inside `blender_execute_blender_code` (online access is on), then `import_assets`.

## Prerequisites

1. Plugin **blender** installed + enabled (copies the add-on into Blender's user extensions).
2. Tools opted in for this chat.
3. Blender **5.1+** open; add-on **MCP** enabled with Allow Online Access; server on `localhost:9876` (auto).

Not connected → `blender_status`, then teach from [references/connection.md](references/connection.md). Never uv / GitHub / zip installs.

## Tools (all are sugar over one `execute` call into Blender)

| Tool | Use |
|------|-----|
| `blender_status` | Ping + Blender version + open file |
| `blender_get_scene_info` | **All** objects (name, type, collection, location, dimensions, verts), collections, materials, mode, selection |
| `blender_get_object_info` | One object: transform, modifiers (with `show_render`), materials, mesh/tri counts, UV layers |
| `blender_get_viewport_screenshot` | Viewport PNG (needs a 3D Viewport; not in `--background`) |
| `blender_get_python_api_docs` | Live bpy docs: `bpy.ops.mesh.primitive_cube_add`, `bpy.types.Mesh`; trailing `*` discovers (`bpy.ops.mesh.primitive_*`). **Call before inventing an operator or property.** |
| `blender_execute_blender_code` | Run Python in Blender — the only mutator |

### Execute contract (HARD)

- `import bpy` yourself; assign a **JSON-friendly dict** to `result` (`result = {"name": ob.name, "verts": len(me.vertices)}`). Not a dict → error. Non-serializable values fall back to `repr` — prefer `.name` over the datablock.
- `print()` returns as `stdout`; exceptions return as the error. No `sys.exit`, `wm.quit_blender`, factory resets (sandboxed).
- **Inspect, then mutate.** First call reads (`bpy.data.*` → `result`), second call changes. Never guess object names — read them.
- **One named object per mutating call.** Primitive add, rename to `SM_*`/`SK_*`, material, modifier, and join are separate calls (save `.blend` before destructive ops). Never a whole chair/prop in one script — the ledger records one revertable row per call; Revert deletes what that call added.
- Renders / bakes may take minutes; wait for the response, never re-issue.

## Core loop (every asset)

1. `blender_get_scene_info` (or screenshot)
2. Plan → load the right subskill below
3. `blender_execute_blender_code`, one object per call (contract above)
4. `blender_get_viewport_screenshot` → compare → fix
5. Ship: [references/uefn_export.md](references/uefn_export.md) (static) or [references/skeletal_export.md](references/skeletal_export.md) (rigged)

Prefer structured tools when they exist. Never invent scene state.

## Scene analysis prompts (out of the box)

These are the official Lab demos — each is one read-only execute, `result` carries the answer:

- **Rename datablocks to match objects** — `for o in bpy.data.objects: if o.data and o.data.users == 1: o.data.name = o.name`; report `renamed: [...]`. Skip shared data (`users > 1`).
- **Material users** — `{m.name: [o.name for o in bpy.data.objects if any(s.material is m for s in o.material_slots)] for m in bpy.data.materials}`; also `m.users` for orphan detection.
- **Highest polycount (linked, render-visible)** — iterate `bpy.context.scene.objects` only (not `bpy.data.objects`), require `o.type == 'MESH'`, use `o.evaluated_get(depsgraph).data` from `bpy.context.evaluated_depsgraph_get()` so Solidify/Subdivision/Array count; sort by `sum(len(p.vertices) - 2 for p in polygons)`. State whether modifiers were included.
- **Document a Geometry Nodes tree** — read `ng.nodes` (`type`, `label`, `inputs/outputs` links via `ng.links`), write findings into `bpy.data.texts.new("GN_Notes")`, add `NodeFrame` nodes with `label` and parent related nodes to them. Details: `geometry_nodes`.
- **Pre-export audit** — `asset_qa`: manifold, single-user materials named `MAT_*`, `SM_`/`SK_` names, no absolute texture paths (`bpy.path.abspath`, `image.filepath.startswith("//")`).

## Route — load subskills with `skill_read_subskill("blender", "<id>")`

### Core
| Id | When |
|----|------|
| `bpy_fundamentals` | bpy data/context/ops model, modes, selection, bmesh, safe scripting |
| `scene_organization` | Naming `COL_`/`SM_`/`SK_`/`MAT_`, collections, units, orphan purge |
| `verify_loop` | Screenshot compare discipline, shading modes, turntables |
| `lookdev_studio` | Studio lights / viewport so screenshots read form |
| `topology_fundamentals` | Poles, edge flow, n-gons, density — why shading/deform fails |
| `scale_library` | Real-world sizes in meters + Fortnite-scale notes |
| `modifiers` | Bevel, Boolean, Mirror, Subdiv, Array, Smooth by Angle, stack order |
| `mesh_cleanup` | Normals, non-manifold, doubles, degenerate, audit script |
| `blockout` | Proportion pass at real-world scale before detail |

### Disciplines
| Id | When |
|----|------|
| `hard_surface` | Sci-fi, weapons, industrial, kitbash, mid-poly + weighted normals |
| `organic_forms` | Soft volumes, subdivision silhouettes, proportional editing |
| `face_topology` | Eye/mouth loops, poles, expression-ready heads |
| `body_anatomy` | Torso/limbs, joint edge flow, proportions |
| `hands_feet` | Fingers, knuckle loops, palms, feet |
| `character_clothing` | Garment shells over body, folds, hidden-face removal |
| `creature_organic` | Monsters, quadrupeds, wings/tails, non-human anatomy |
| `props` | Everyday / hero props, budgets, origins |
| `vehicles` | Cars, ships, mechs, movable parts + pivots |
| `environments_modular` | Modular kits, grid math, pivots, trim sheets |
| `vegetation` | Trees, plants, foliage cards, scatter |

### Pipeline
| Id | When |
|----|------|
| `sculpting` | Massing beyond box modeling; what is/isn't scriptable |
| `sculpt_brushes` | Use real sculpt brushes headless — scripted strokes, masks, mesh filters (smooth faces, creases, clay) |
| `retopology` | Game-ready quads over sculpt/AI mesh, quadriflow, shrinkwrap |
| `uv_workflow` | Seams, unwrap, texel density, packing, lightmap channel |
| `trim_sheets` | Shared atlas / trim UVs for modular env + hard-surface |
| `materials_shading` | Principled PBR node graphs (4.x socket names) |
| `texture_bake` | High→low normals/AO/color, cage, green channel for UE |
| `hair_groom` | Hair cards for games, Curves hair, baking hair textures |
| `cloth` | Cloth sim as fold generator, pin groups, freeze result |

### Rig & Animate
| Id | When |
|----|------|
| `rigging_armatures` | Build armatures/bones in code, constraints, bone collections, Rigify |
| `skinning_weights` | Auto weights, vertex groups, influence limits, weight transfer |
| `shape_keys` | Morph targets, corrective shapes, drivers, facial sets |
| `animation_actions` | Keyframes, actions (slotted 4.4+), NLA, baking for export |

### Import & Ship
| Id | When |
|----|------|
| `import_assets` | Import FBX/glTF/OBJ/USD into Blender, fix scale/axes, clean AI meshes |
| `geometry_nodes` | Procedural arrays / scatter / generators; realize before export |
| `lod_collision` | LOD chain + UCX collision meshes |
| `asset_qa` | Runnable audit + checklist before export |
| `reference_match` | Photo → analyze → build → compare |
| `skeletal_export` | Rigged/animated FBX → UEFN (skeleton, morphs, anims) |
| `uefn_export` | Static FBX/glTF → UEFN, failure table |
| `connection` | Official add-on / socket troubleshooting, Blender 5.1 requirement |

## Don'ts

- Don't wipe the scene without user confirmation.
- Don't tell users to install uv, clone blender-mcp from GitHub, or add a Blender MCP server to their IDE — Ducky is the server.
- Don't invent `bpy.ops.*` names — `blender_get_python_api_docs` first.
- Don't return Blender datablocks in `result` — return names/numbers.
- Don't ship raw AI/Studio meshes for deforming characters — retopo first.
- Don't mix Studio API setup into this plugin — use **studio3d**.
