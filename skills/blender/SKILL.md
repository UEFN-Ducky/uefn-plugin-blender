---
name: blender
description: "Control Blender via UEFN-Ducky — model anything with bpy (hard surface, faces, characters, organic, props, env), rig/skin/animate, cloth & hair, UVs/materials/baking, Poly Haven / Sketchfab / Hyper3D, screenshot verify loops, import/export to UEFN"
license: All Rights Reserved
metadata:
  label: Blender
  version: 6
  author: Iliya Kovachki
  copyright: Copyright 2026 Iliya Kovachki
  allow_redistribute: false
  managed_by: uefn-ducky
  source_plugin_id: blender
---

# Blender — director (model in Blender via MCP)

You drive Blender through the **blender** Store plugin (`blender_*` on shared `uefn-ducky` MCP). No nested uvx / separate Blender MCP server.

**Blender-only work does NOT need the UEFN editor.** If Blender is connected, proceed — do not wait for Fortnite.

**Path choice:** modeling can be Blender **or** UEFN. If unclear, ask once. Export-to-UEFN is a later step.

**SaaS generation:** Install Store plugin **meshy** (`meshy_*`) or **studio3d** (`studio3d_*`). Then import / clean / export here. Those plugins are **not** part of this one.

## Prerequisites

1. Plugin **blender** installed + enabled.
2. Tools opted in for this chat.
3. Blender open, BlenderMCP addon enabled, listening on `localhost:9876`.
4. Disable any old nested `blender` / `uvx blender-mcp` in IDE mcp.json.

Not connected → teach the user: [references/connection.md](references/connection.md). Short path: Preferences → Add-ons → enable Blender MCP → N → Connect → `blender_status`.

## Core loop (every asset)

1. `blender_get_scene_info` (or screenshot)
2. Plan → load the right subskill below
3. Small `blender_execute_blender_code` steps (save `.blend` before destructive ops)
4. `blender_get_viewport_screenshot` → compare → fix
5. Ship: [references/uefn_export.md](references/uefn_export.md) (static) or [references/skeletal_export.md](references/skeletal_export.md) (rigged)

Prefer structured tools when they exist. Never invent scene state.

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
| `connection` | Addon / socket troubleshooting |

## Optional Blender-addon integrations

Keys in BlenderMCP sidebar prefs:

- Poly Haven / Sketchfab / Hyper3D Rodin / Hunyuan3D (`blender_get_*_status` → generate/download → import)

## Don'ts

- Don't wipe the scene without user confirmation.
- Don't tell users to install uv or download addon.py from GitHub.
- Don't ship raw AI/Studio meshes for deforming characters — retopo first.
- Don't mix Studio API setup into this plugin — use **studio3d**.
