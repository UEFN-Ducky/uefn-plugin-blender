---
description: "Realistic human head recipes by sex, age and build, with anatomical slider recipes (no ethnic presets) and the full build order from blockout to rig-ready head"
metadata:
  label: "Realistic humans"
---

# Realistic human heads

Pick sex, age and build, then dial measured features with sliders (−1..1). Never use ethnicity presets: they stereotype. Measure the reference (nose width vs. inner-eye gap, lip height, jaw width, eye tilt) and set sliders to match.

| Archetype | Forge `head` call | Read |
|---|---|---|
| Rugged soldier | `{"sex":"male","build":"heavy","shape":{"jaw_width":0.6,"brow":0.5,"chin":0.4}}` | square jaw, heavy brow |
| Elegant lead | `{"sex":"female","build":"slim","shape":{"cheekbone":0.6,"lip_full":0.4,"eye_tilt":0.3}}` | high cheekbones, full lips |
| Kid sidekick | `{"age":"child","shape":{"eye_size":0.4,"nose_length":-0.4}}` | low eye line, small nose |
| Old mentor | `{"age":"elder","sex":"male","shape":{"nose_length":0.4,"brow":0.3}}` | deep folds, thin lips |
| Neutral NPC | `{"sex":"neutral","build":"average"}` | crowd base for variation |

Sliders: `face_width skull_depth jaw_width chin cheekbone brow nose_width nose_length nose_bridge lip_full mouth_width eye_size eye_tilt eye_spacing`. For crowds, randomise each slider in ±0.4 and the tone in 0–1; keep `eye_spacing` within ±0.3 (outside that range the face reads uncanny).

## Build order

1. Blockout and proportions: `../character-artist/references/head-blockout.md` (or Forge `head`).
2. Loops and poles: `../character-artist/references/bpy-face-topology.md`.
3. Sculpt passes: `../character-artist/references/face-sculpt-passes.md`.
4. Eyes, teeth, mouth bag: `../character-artist/references/eyes-teeth.md`.
5. Skin shader: `../realistic-style/references/skin-sss.md`.
6. Likeness against refs: `../character-artist/references/face-likeness.md`.
7. Blendshapes: `../character-artist/references/facs-blendshapes.md`.
8. Hair: `../character-artist/references/hair-handoff.md`.

## Done when

Front, three-quarter and side renders read as the archetype at thumbnail size (128 px), and the eye line sits at 0.5 H (0.44 H for a child).

---
MIT, uefn-ducky; own words.
