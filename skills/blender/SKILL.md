---
name: blender
description: "Control Blender 5.1+ via UEFN-Ducky and the official Blender Lab MCP add-on — model anything with bpy (hard surface, faces, characters, organic, props, env), rig/skin/animate, cloth & hair, UVs/materials/baking, scene analysis (polycount, material users, datablock renames), screenshot verify loops, import/export to UEFN"
license: MIT
metadata:
  label: Blender
  version: 10
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
2. Blender **5.1+** open. Socket is locked to `localhost:9876` — no Settings, no Preferences.

Not connected → `blender_status` (it heals). Never uv / GitHub / zip installs. Never tell anyone to tick MCP, allow online access, or type a port.

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
2. Plan → load the right pack or blender subskill below
3. `blender_execute_blender_code`, one object per call (contract above)
4. `blender_get_viewport_screenshot` → compare → fix
5. Ship: `skill_read_subskill("blender", "uefn_export")` (static) or `skill_read_subskill("blender", "skeletal_export")` (rigged)

Prefer structured tools when they exist. Never invent scene state.

**Reference photo attached:** fill `skill_read_subskill("blender", "reference_analysis_template")` before mutating, then `reference_match`. Match camera before micro-detail.

## Scene analysis prompts (out of the box)

These are the official Lab demos — each is one read-only execute, `result` carries the answer:

- **Rename datablocks to match objects** — `for o in bpy.data.objects: if o.data and o.data.users == 1: o.data.name = o.name`; report `renamed: [...]`. Skip shared data (`users > 1`).
- **Material users** — `{m.name: [o.name for o in bpy.data.objects if any(s.material is m for s in o.material_slots)] for m in bpy.data.materials}`; also `m.users` for orphan detection.
- **Highest polycount (linked, render-visible)** — iterate `bpy.context.scene.objects` only (not `bpy.data.objects`), require `o.type == 'MESH'`, use `o.evaluated_get(depsgraph).data` from `bpy.context.evaluated_depsgraph_get()` so Solidify/Subdivision/Array count; sort by `sum(len(p.vertices) - 2 for p in polygons)`. State whether modifiers were included.
- **Document a Geometry Nodes tree** — read `ng.nodes` (`type`, `label`, `inputs/outputs` links via `ng.links`), write findings into `bpy.data.texts.new("GN_Notes")`, add `NodeFrame` nodes with `label` and parent related nodes to them. Details: `skill_read_subskill("geometry-nodes")`.
- **Pre-export audit** — `skill_read_subskill("qa-review")`: manifold, single-user materials named `MAT_*`, `SM_`/`SK_` names, no absolute texture paths (`bpy.path.abspath`, `image.filepath.startswith("//")`).

## Route — blender pack subskills (`skill_read_subskill("blender", "<id>")`)

Ducky bpy + UEFN ship. Load `core` (this file) for the execute contract.

### Core
| Id | When |
|----|------|
| `bpy_fundamentals` | bpy data/context/ops model, modes, selection, bmesh, safe scripting |
| `scene_organization` | Naming `COL_`/`SM_`/`SK_`/`MAT_`, collections, units, orphan purge |
| `verify_loop` | Screenshot compare discipline, shading modes, turntables |
| `topology_fundamentals` | Poles, edge flow, n-gons, density — why shading/deform fails |
| `scale_library` | Real-world sizes in meters + Fortnite-scale notes |
| `modifiers` | Bevel, Boolean, Mirror, Subdiv, Array, Smooth by Angle, stack order |
| `mesh_cleanup` | Normals, non-manifold, doubles, degenerate, audit script |
| `blockout` | Proportion pass at real-world scale before detail |
| `organic_forms` | Soft volumes, subdivision silhouettes, proportional editing (bpy, no brushes) |
| `sculpt_brushes` | Headless sculpt strokes, masks, mesh filters |
| `trim_sheets` | Shared atlas / trim UVs bpy |
| `polycount_budgets` | Triangle budgets by asset class |
| `style_routing` | Engine/phase/style matrix for specialist packs |
| `reference_match` | Photo → analyze → build → compare |
| `reference_analysis_template` | Fill before MCP when a reference image is attached |
| `import_assets` | Import FBX/glTF/OBJ/USD, fix scale/axes, clean AI meshes |
| `skeletal_export` | Rigged/animated FBX → UEFN |
| `uefn_export` | Static FBX/glTF → UEFN (not generic Unreal — that is pack `unreal-export`) |
| `connection` | Official add-on / socket troubleshooting, Blender 5.1 requirement |

## Route — specialist packs (`skill_read_subskill("<pack-id>")`)

Omit subskill id to list refs. `core` is that pack's SKILL.md. Folded bpy recipes are `bpy-*` stems. **UEFN export always** `skill_read_subskill("blender", "uefn_export")`.

### Disciplines
| Pack | When |
|------|------|
| `hard-surface` | Sci-fi, weapons, industrial, kitbash, mid-poly + weighted normals |
| `prop-artist` | Everyday / hero props, kitbash, furniture |
| `vehicle-artist` | Cars, ships, mechs, movable parts + pivots |
| `environment-artist` | Modular kits, grid math, pivots, trim sheets |
| `vegetation-artist` | Trees, plants, foliage cards, scatter |
| `character-artist` | Anatomy, clothing, facial topology, hands/feet |
| `creature-artist` | Monsters, quadrupeds, wings/tails |
| `character-archetypes` | Races/roles (elf, mecha, knight, …) |

### Pipeline
| Pack | When |
|------|------|
| `sculpting` | Massing beyond box modeling |
| `retopology` | Game-ready quads over sculpt/AI mesh |
| `uv-workflow` | Seams, unwrap, texel density, packing |
| `blender-materials` | Principled PBR / stylized shading (`materials` is a different Store plugin) |
| `texture-workflow` | High→low bake, atlases |
| `hair-groom` | Hair cards, Curves hair |
| `cloth-sim` | Cloth sim as fold generator |
| `lookdev` | Studio lights / viewport so screenshots read form |
| `geometry-nodes` | Procedural arrays / scatter / generators |
| `procedural-modeling` | Rocks, roads, cables, buildings (procedural) |
| `lighting` | Mood, cinematic lighting |
| `camera-cinematography` | Lenses, framing, camera moves |
| `rendering` | Final renders, passes |
| `compositing` | Grade, beauty stack |
| `vfx-fx` | Smoke, fire, particles |
| `physics-sim` | Rigid/soft body, destruction |
| `rigging` | Bones, IK, weights, shape keys |
| `blender-animation` | Keyframes, NLA, cycles (`animation` is a different Store plugin) |
| `scene-assembly` | Large scene layout, linking |
| `set-dressing` | Prop placement, narrative clutter |
| `archviz` | Interiors/exteriors |
| `asset-optimization` | Polycount, cleanup |
| `lod-pipeline` | LOD chain |
| `collision-proxy` | UCX / convex colliders |
| `export-pipeline` | Generic FBX/glTF/USD |
| `unreal-export` | Generic Unreal FBX/UCX (UEFN still uses `uefn_export`) |
| `unity-export` | Unity GLB/FBX |
| `godot-export` | Godot glTF |
| `qa-review` | Audit + checklist before export |

### Style / world / genre (compact)

Load `skill_read_subskill("blender", "style_routing")` for the full matrix. Signals:

- Horror: `horror-style`, `psx-horror-style`, `cosmic-eldritch-horror`, `body-horror-style`, `analog-found-footage-horror`, `liminal-space-style`, `folk-horror-style`, `mascot-puppet-horror`, `dream-weirdcore-style`, `indie-horror-aesthetics`
- Look: `lowpoly-style`, `anime-style`, `manga-style`, `cartoon-style`, `comic-book-style`, `voxel-style`, `isometric-style`, `stylized-style`, `realistic-style`, `pixel-art-style`, `hd-2d-style`, `hand-painted-style`, `painterly-style`, `stop-motion-craft-style`, `chibi-style`, `noir-style`, `minimalist-style`, `vector-style`, `frutiger-aero-style`, `retro-8bit-style`, `retro-16bit-style`
- Mood/world: `cozy-wholesome-mood`, `dark-gritty-mood`, `dream-surreal-mood`, `neon-retrofuturism`, `brutalist-mood`, `fantasy-worlds`, `sci-fi-punk-worlds`, `historical-worlds`, `apocalypse-worlds`, `biome-worlds`, `visual-console-eras`
- Genre: `genre-action-combat`, `genre-shooter`, `genre-rpg`, `genre-survival`, `genre-stealth`, `genre-puzzle-platformer`, `genre-metroidvania-roguelike`, `genre-soulslike`, `genre-strategy-sim`, `genre-racing-sports`, `genre-narrative-vn`, `genre-card-party-idle`, `genre-open-world-sandbox`

## Don'ts

- Don't wipe the scene without user confirmation.
- Don't tell users to install uv, clone blender-mcp from GitHub, or add a Blender MCP server to their IDE — Ducky is the server.
- Don't invent `bpy.ops.*` names — `blender_get_python_api_docs` first.
- Don't return Blender datablocks in `result` — return names/numbers.
- Don't ship raw AI/Studio meshes for deforming characters — retopo first.
- Don't mix Studio API setup into this plugin — use **studio3d**.
- Don't load Store packs `animation` or `materials` for Blender work — those are other plugins; use `blender-animation` and `blender-materials`.
