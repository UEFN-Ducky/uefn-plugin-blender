---
name: genre-shooter
description: Art direction for FPS, TPS, shooter, battle royale, and extraction-shooter maps and props in Blender with sightline and cover language.
license: MIT
metadata:
  managed_by: uefn-ducky
  source_plugin_id: blender
  author: https://github.com/arjun988
  version: "1.0.0"
  domain: blender
  role: specialist
  triggers: shooter, FPS, TPS, battle royale, extraction shooter, cover shooter, gun game art
  related-skills: environment-artist, hard-surface, prop-artist, collision-proxy, scene-assembly
---

# Genre: Shooter

Sightlines. Cover. Landmarking. Loot readability. Scale for camera height (FPS vs TPS).

## Weapons

Real size first, then one exaggeration. Origin at the grip, muzzle down the engine's forward axis, sockets `Muzzle` / `Sight` / `Magazine` / `Grip`. Budget by camera: FPS 8-20k tris, TPS 3-6k, pickup 1-3k, 3 materials or fewer. Fastest path: Forge `{"tool": "forge_hq", "op": "weapon", "params": {"kind": "rifle"}}` (11 kinds, realistic | stylized).

Done when: the side render shows grip, trigger guard, mag and sight as separate shapes, and tris / materials fit the budget row.

## Reference Guide

| Topic | Reference | Load When |
|-------|-----------|----------|
| FPS vs TPS spaces | `references/fps-tps.md` | Camera scale, framing |
| Battle royale / extraction | `references/br-extraction.md` | Map layout |
| Weapon budgets (tris, textures, LODs, FOV) | `references/weapon-budgets.md` | Any gun or melee asset |
| Weapon proportions | `../hard-surface/references/weapons-proportions.md` | Blockout |
| Parts, origin, sockets per engine | `../hard-surface/references/weapons-modular.md` | Part kit, export |
| Hard-surface stack, edges, wear | `../hard-surface/references/weapons-surface.md` | Bevels, materials |
| Sci-fi shape language | `../hard-surface/references/weapons-scifi.md` | Sci-fi or energy weapons |
