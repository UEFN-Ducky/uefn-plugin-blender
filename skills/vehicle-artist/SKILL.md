---
name: vehicle-artist
description: Dedicated vehicle modeling for cars, trucks, aircraft, ships, boats, mechs, and transit assets with proportion, panel flow, and game LOD awareness in Blender via MCP.
license: MIT
metadata:
  managed_by: uefn-ducky
  source_plugin_id: blender
  author: https://github.com/arjun988
  version: "1.0.0"
  domain: blender
  role: specialist
  triggers: vehicle, car, truck, aircraft, plane, ship, boat, mech, tank, motorcycle, transit, chassis, bodywork
  related-skills: hard-surface, blender, blender-materials, lod-pipeline, collision-proxy, export-pipeline
---

# Vehicle Artist

Proportion-driven vehicles. Clear body language. Manufacturing panel flow. Engine-ready LODs.

## When to Use

- Cars, trucks, bikes, aircraft, boats, ships
- Mechs and large mechanical walkers
- Transit / industrial vehicles
- When vehicle work should not live under generic hard-surface

## Design Principles

1. **Proportion blockout first** — Wheelbase, cabin, mass distribution
2. **Centerline symmetry** — Mirror early; break only for damage/wear
3. **Panel flow** — Seams follow stamped/assembled construction
4. **Functional readability** — Lights, intakes, doors, wheels read clearly
5. **Separate systems** — Body, wheels, glass, interior, lights as objects

## Workflow

```
Ortho refs → Chassis blockout → Body volumes → Wheel/suspension
  → Panel breaks → Booleans/cutters → Bevels → Glass/lights
  → Interior (LOD-aware) → UVs → Materials → LODs → Collision → Export
```

## Every part on its own

Each car part is its own object with its origin at its mount point (wheel → hub, door → hinge, light → mount), real cm sizes and shared material slots, so any part fits any car of the same size class: build it alone, swap it in, keep the transform. Right-side parts: mirror and apply scale (lights, mirrors, doors) or turn 180° about Z (wheels, plates: text must read).

## Blockout Checklist

- [ ] Overall length / width / height locked
- [ ] Wheel size and stance correct
- [ ] Cabin / canopy silhouette readable
- [ ] Ground clearance intentional
- [ ] Symmetry axis established

## Object Split (Game)

| Object | Why |
|--------|-----|
| `SM_Vehicle_Body` | Main shell |
| `SM_Vehicle_Wheel_*` | Spin / steer |
| `SM_Vehicle_Glass` | Transparency / sorting |
| `SM_Vehicle_Light_*` | Emissive materials |
| `SM_Vehicle_Interior` | Cull on distant LODs |

## LOD Guidance

| LOD | Focus |
|-----|-------|
| LOD0 | Full panels, interior if visible |
| LOD1 | Simplified panels, remove micro |
| LOD2 | Body + wheels + glass only |
| LOD3 | Impostor / ultra-low hull |

Use `lod-pipeline` for generation and validation.

## Collision

- Simple convex hulls per major volume
- Wheel capsules/cylinders separate if physics-driven
- See `collision-proxy`

## Constraints

### MUST DO
- Lock proportions before panel detail
- Keep wheels as separate objects when animated
- Plan LODs and collision with body

### MUST NOT DO
- Detail interior before exterior silhouette
- Boolean chaos without cutter collection
- Single merged mesh for all systems on game vehicles

## Reference Guide

| Topic | Reference | Load When |
|-------|-----------|----------|
| Car body from curves: proportions per body style, blueprints, section loft, panels with 4 mm gaps, arches | `references/car-body-from-curves.md` | Any car, truck, van, limo or kart body |
| Tire from a size code (225/45R17), tread, sidewall text | `references/parts/tire-from-size.md` | Tires, wheels |
| Rim and spokes (5 / 10 / mesh / dish / n), lug nuts | `references/parts/rim-spokes.md` | Rims, wheels |
| Brake disc, caliper, suspension coilover and arms | `references/parts/brakes-suspension.md` | Brakes, suspension |
| Headlight, taillight (reflector, lens, emissive), grille | `references/parts/lights-grille.md` | Lights, grilles |
| Door with inner panel and hinge, hood, trunk, fender arch, window, mirror | `references/parts/panels-door-hood.md` | Body panels and openings |
| Bumpers, spoiler (airfoil), diffuser, exhaust, license plate, wiper | `references/parts/bumpers-aero-exhaust.md` | Bolt-on exterior parts |
| Seat, steering wheel, dashboard, engine | `references/parts/interior-engine.md` | Interior and engine bay |
| Car paint (flakes, clearcoat 1.0 / 0.03), glass, chrome, rubber | `references/car-paint-materials.md` | Car materials |
| Vehicle rig for UE / UEFN (FL_wheel…, doors), LODs, UCX | `references/vehicle-rig-ue.md` | Rigging, exporting a car |
| Proportion Blockout | `references/proportion-blockout.md` | When needed |
| Vehicle Object Split | `references/vehicle-object-split.md` | When needed |
| Vehicle Lod Targets | `references/vehicle-lod-targets.md` | When needed |
| Mid-poly stack, panel / vent / bolt kits | `../hard-surface/references/midpoly-stack.md`, `../hard-surface/references/detail-kits.md` | Body panels, grilles, bolts |
