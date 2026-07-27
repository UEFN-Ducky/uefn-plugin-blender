# Body anatomy

Torso and limb topology built for deformation: proportions, landmark loops, joint bend zones, mirror workflow, and skinning prep. Load for any humanoid/biped body work between blockout and rigging.

## Proportions: heads-tall system

One head unit = total height / heads. Work in meters at real scale (UEFN character capsule ≈ 1.9 m).

| Style | Heads tall | Use |
|---|---|---|
| Realistic average | 7.5 | grounded NPCs |
| Idealized / heroic | 8 | default for game heroes — reads best at gameplay camera distance |
| Fashion / superhero | 8.5–9+ | exaggerated stylization |

Torso is ~3 heads regardless of style: chin→nipple, nipple→navel, navel→perineum. Knees sit roughly midway between perineum and ground.

Drop guide empties before modeling and keep them until final proportion check:

```python
import bpy
H, heads = 1.9, 8.0            # 1.9 m = Fortnite/UEFN capsule; 7.5 realistic, 8.5+ stylized
u = H / heads
marks = {"crown": 8.0, "chin": 7.0, "nipple": 6.0, "navel": 5.0,
         "crotch": 4.0, "knee": 2.0, "ankle": 0.35}
col = bpy.context.collection
for name, k in marks.items():
    e = bpy.data.objects.new(f"GUIDE_{name}", None)
    e.empty_display_type = 'PLAIN_AXES'
    e.empty_display_size = 0.3
    e.location = (0.0, 0.0, k * u)
    col.objects.link(e)
```

## Landmark-driven loops

Edge loops follow bone/muscle landmarks, not arbitrary grid lines. Loops along the dominant muscle grain stretch cleanly under linear-blend skinning.

| Landmark | Loop it drives |
|---|---|
| Clavicle | horizontal loop across upper chest → shoulder; anchors shrug/reach deformation |
| Deltoid | radial fan from the shoulder cap, flowing into both pectoral and scapula loops |
| Sternum / pec line | chest loops sweep from sternum out under the armpit |
| Iliac crest / pelvis | belt-line loop; separates soft abdomen from rigid pelvis |
| Glute / quad | hip loops wrap glute and continue down the quad grain |
| Spine | vertical center loop, denser horizontals at the waist |

Jawline/neck flow is covered in `face_topology`; wrists hand off to `hands_feet`.

## Joint topology: elbow and knee (3-loop bend zone)

- Place one loop **exactly on the bend crease** (elbow point, back of knee).
- Standard pattern: **3 loops on the outside of the bend** (back of elbow, front of knee) with the middle loop terminating so the **inside of the bend carries only 2** — outside keeps volume, inside avoids crumpling. Minimum viable: 2 full loops around the joint.
- Keep the bend zone all-quad with even spacing; no poles on or next to the crease.

Scripted full-ring insertion — bisect at the pivot and at ± offsets (the terminated inner loop is a manual retopo refinement; full rings are fine for game density):

```python
import bpy, bmesh
ob = bpy.context.object                     # limb/body mesh, object mode
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
knee_z = 0.5225                             # joint pivot height (m) — match the bone head
for dz in (-0.03, 0.0, 0.03):               # support / crease / support
    bm = bmesh.new(); bm.from_mesh(ob.data)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    # NOTE: bisect cuts ALL geometry crossing the plane; to limit it to one limb,
    # build geom from selected elements only (v.select / e.select / f.select).
    bmesh.ops.bisect_plane(bm, geom=geom,
                           plane_co=(0.0, 0.0, knee_z + dz), plane_no=(0.0, 0.0, 1.0))
    bm.to_mesh(ob.data); bm.free()
ob.data.update()
```

For arms in T/A-pose, set `plane_no` along the limb axis (e.g. `(1,0,0)` for a T-pose arm) instead of Z.

## Shoulder and hip flow

- **Shoulder**: deltoid fan radiates from the shoulder cap and merges into chest and back loops. Hide the unavoidable pole **in the armpit** — it is compressed and shadowed there.
- **Hip**: loops wrap the glute and flow down the quad/hamstring grain; hide the crotch pole in the **inner-thigh crease**.
- Model with a slight A-pose or match the target skeleton's rest pose — extreme T-pose banks all shoulder range into the arms-down direction.
- 5-poles are fine in flat, low-deformation zones (armpit, inner thigh, side of ribcage); never on the shoulder cap or glute peak.

## Spine / torso loop density

- **Ribcage is rigid** — it barely deforms; 2–3 horizontal loops are enough.
- **Waist/abdomen bends and twists** — put 3+ evenly spaced horizontal loops between ribcage and pelvis so spine bend and twist distribute instead of shearing one ring.
- One loop at the clavicle line, one under the pecs, one at the navel/waist, one at the iliac crest is the minimal skeleton of torso loops.

## Density budgeting: spend where it bends

| Region | Density | Why |
|---|---|---|
| Shoulders, hips | high | largest rotation range, multi-axis |
| Elbows, knees | high (3-loop zones) | hinge crease |
| Wrists, ankles | medium | clean loop ring for weight cutoff |
| Waist | medium-high | bend + twist |
| Ribcage, skull, mid-shaft limbs | low | near-rigid |

Limb cross-sections (cylinder sides): 8 for low-poly/mobile, 12–16 standard game, 24+ hero closeup. Set these at `blockout` time — adding sides later is painful.

## Mirror workflow

Model half, mirror across X. Apply the mirror **before** asymmetric detailing, before shape keys (shape keys block `modifier_apply`), and before skinning unless you deliberately weight with symmetry tools (see `skinning_weights`).

```python
import bpy
ob = bpy.context.object
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)  # mirror axis = object origin
m = ob.modifiers.new("Mirror", 'MIRROR')
m.use_axis[0] = True                # X
m.use_clip = True                   # lock center verts to the seam
m.merge_threshold = 0.001
# ... symmetric modeling happens here ...
bpy.ops.wm.save_mainfile()          # checkpoint before the destructive step
bpy.ops.object.modifier_apply(modifier=m.name)   # object must be active; multi-user data needs single_user=True
```

If symmetry drifted on an already-full mesh, edit mode `bpy.ops.mesh.symmetrize(direction='POSITIVE_X')` rebuilds one side from the other.

## Game budgets

| Tier | Budget | Source |
|---|---|---|
| MetaHuman body (Epic) | 30,500 / 7,600 / 3,350 / 1,507 verts LOD0→3 | Epic LOD specs |
| AAA hero w/ cinematics | ~250k tris total (gameplay mesh ~2/3) | community consensus |
| Mid-tier stylized hero | 50–60k tris | community consensus |
| Indie main character | 11–13k tris | community consensus |

UEFN specifics: skinned meshes get **no Nanite benefit**, so real LODs and lean base density matter; prefer one material section per mesh; textures ≤ 2K. Full export rules live in `skeletal_export`.

## Prepping for skinning

- Put an edge loop **exactly at every joint pivot** — weights fall off cleanly across a ring instead of smearing over a span. Read pivots from the armature instead of eyeballing:

```python
import bpy, bmesh
arm = bpy.data.objects["RIG_Body"]
ob  = bpy.data.objects["SK_Body"]
for bone, axis in (("shin.L", (0, 0, 1)), ("forearm.L", (1, 0, 0))):  # normal = limb direction
    co_world = arm.matrix_world @ arm.data.bones[bone].head_local     # bone head = joint pivot
    co_local = ob.matrix_world.inverted() @ co_world
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
                           plane_co=co_local, plane_no=axis)
    bm.to_mesh(ob.data); bm.free()
ob.data.update()
```

- Apply scale (`transform_apply`) before parenting to the armature — non-uniform object scale corrupts bind math.
- Keep bend zones quad-only; triangles and poles there produce candy-wrapper pinches.
- Wrist and ankle rings double as weight boundaries for glove/boot material splits and for `character_clothing` seams.
- Rig setup itself: `rigging_armatures`; weights: `skinning_weights`.

## Scale / proportion verification

```python
import bpy
d = bpy.context.object.dimensions
print(f"H {d.z:.3f} m  W {d.x:.3f}  D {d.y:.3f}")   # target height ≈ 1.9 m for UEFN
```

Height off by 10x or 100x means a units mistake — fix the mesh, not the object scale. Compare silhouette against the GUIDE empties in an orthographic front view.

## Verify

- `blender_get_viewport_screenshot` front + side orthographic in rest pose: chin/nipple/navel/crotch land on the GUIDE empties; limbs read as the intended heads-tall style.
- Wireframe screenshot of elbow and knee: loop on the crease, 3 rings outside the bend, quads only.
- `blender_get_object_info`: vert count within the target budget row above; `dimensions.z` ≈ 1.9.
- After mirror apply: no visible center seam, no doubled verts along X=0 (clip + merge handled it).

## Don'ts

- Poles or triangles on bend creases — they pinch the moment the joint rotates.
- Uniform density everywhere: a dense ribcage wastes budget the elbows needed.
- Diagonal "spaghetti" flow across elbows/knees instead of perpendicular rings.
- Applying mirror after shape keys exist — `modifier_apply` refuses; order is mirror → apply → shape keys.
- Fixing wrong world size with object scale instead of applying it — bind pose and export both break.
- Detailing asymmetry (scars, gear) before the mirror is applied — it gets duplicated to both sides.

See also: `blockout`, `face_topology`, `hands_feet`, `character_clothing`, `skinning_weights`, `rigging_armatures`, `skeletal_export`, `verify_loop`.
