---
description: "Look-dev review settings: Khronos PBR Neutral for true colour checks, AgX for final, Standard only for flat UI art; the 18 % grey test, which light preset per check, and the 3-5 pass cap"
metadata:
  label: "Review Transforms"
---

# Review Transforms

| View transform | Use | bpy |
|---|---|---|
| Khronos PBR Neutral | judge albedo and material colour: hues stay true, highlights roll off | `scene.view_settings.view_transform = "Khronos PBR Neutral"` |
| AgX | final renders, wide light range | `"AgX"` (Look: Base Contrast; Punchy for stylized) |
| Standard | flat UI art, colour-picked palettes; clips bright light | `"Standard"` |

Checks, each a still from `lighting` → `lookdev-light-presets`:

| Check | Preset | Pass when |
|---|---|---|
| albedo values | neutral + Khronos PBR Neutral | no pure black or white; metals bright, charcoal ≥ sRGB 30 |
| material read | studio (18 % grey cove) | metal reads as metal, roughness change visible |
| form / silhouette | dramatic | silhouette readable, edge wear catches the rim |
| hero / store shot | product | clean, no clipped highlight |
| outdoor prop | env noon, then golden | colour holds in warm light |

- One change per pass (material **or** light **or** camera), a still after each, stop after 3-5 passes: a sixth pass is guessing, list the gaps instead.
- Exposure: AgX 0 for studio; +1.5 only for night scenes.

Adapted from Blender Agent Skills by EL4CTEO (lookdev, rendering; MIT). Same transforms as Forge `light(transform=agx|neutral|standard)`.
