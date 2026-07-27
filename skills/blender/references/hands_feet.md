# Hands and feet

Load when modeling or fixing hands, fingers, thumbs, feet, or toes on a character — topology, budgets, scripted construction, and where the rig joints go. Body-wide loop flow lives in `body_anatomy`; this file is extremities only.

## Proportions (1.9 m UEFN character reference)

| Part | Size | Notes |
|---|---|---|
| Hand (wrist → middle fingertip) | ~18–19 cm | ≈ face height (chin → hairline) |
| Palm | ~10 cm long × 9 cm wide × 3 cm thick | middle finger ≈ palm length |
| Finger center-to-center at knuckles | ~2 cm | pinky noticeably thinner than index |
| Foot | ~26 cm long × 9 cm wide | heel to toe |
| Ankle pivot height | ~7–8 cm above sole | between the malleoli |

Knuckle line is an **arc**, not a straight row — middle finger knuckle sits furthest forward, pinky furthest back. Fingers fan slightly outward from a point near the wrist. Model in a **relaxed pose**: fingers gently curled (~10–15° at each joint) and spread with visible gaps — never flat and splayed, never touching.

## Hand topology rules

- **3 loops per knuckle** (MCP, PIP, DIP): one exactly on the joint crease plus one support loop on each side. A lone crease loop collapses when the finger curls; the supports hold volume. Density priority: knuckles > finger shafts > palm center.
- **Palm fan**: loops flow radially from the wrist through the metacarpals and terminate cleanly into each finger — the finger tubes are continuations of palm loops, not glued-on cylinders.
- **Thumb saddle**: the CMC joint (base of thumb, inside the palm) needs its own dedicated loops — the thumb rotates through opposition here, the widest range of motion in the hand. Expect a 5-pole at the saddle; park it on the palm side, off the deforming crest.
- **Webbing**: a small skin bridge between finger bases (one quad row deep). It stops silhouette gaps at the finger roots and gives skinning a blend zone.
- **Finger spacing for rigging**: keep an air gap between finger shafts at least one edge-width wide. Automatic weights (voxel/heat) bleed between touching fingers and you will spend hours painting it out.
- All-quad in deforming zones. A triangle fan capping the fingertip is fine — nothing bends there. Nails: for game hands, a crease loop or just texture; separate nail geometry is hero-only.

## Budgets by LOD (mitten vs full fingers)

| Tier | Fingers | Loops per knuckle | Tris per hand |
|---|---|---|---|
| Hero / LOD0 | 5 separate | 3 | ~1,000–2,000 (commonly cited norm) |
| Standard game character | 5 separate | 2–3 | ~400–800 |
| Low-poly (≤2k-tri body) | mitten + separate thumb | 1–2 | 150–250 |
| Distant LOD | full mitten, thumb fused | — | <100 |

The thumb is the last thing to fuse — a mitten with an opposable thumb still reads as a hand; a full mitten only works at distance. Skinned meshes get no Nanite benefit in UEFN, so these LODs are real savings — see `lod_collision`.

## Scripted hand: build one finger, duplicate, vary

Fingers are near-identical tubes — build one procedurally with the knuckle loops baked in, then instantiate four with per-finger length/radius/offset. Runs as-is via `blender_execute_blender_code` (meters, +Y = finger direction).

```python
import bpy, bmesh, math
from math import radians

def make_finger(name, length, radius, segs=8):
    # Ring positions along the finger: base, then 3 loops per knuckle
    # (support / crease / support) at PIP ~0.45 and DIP ~0.75, then tip.
    fracs = [0.0, 0.15, 0.40, 0.45, 0.50, 0.70, 0.75, 0.80, 0.93, 1.0]
    bm = bmesh.new()
    rings = []
    for f in fracs:
        taper = 1.0 - 0.35 * f  # fingers thin toward the tip
        rings.append([bm.verts.new((math.cos(a) * radius * taper,
                                    f * length,
                                    math.sin(a) * radius * taper))
                      for a in (i * 2 * math.pi / segs for i in range(segs))])
    for ra, rb in zip(rings, rings[1:]):
        for i in range(segs):
            bm.faces.new((ra[i], ra[(i + 1) % segs], rb[(i + 1) % segs], rb[i]))
    tip = bm.verts.new((0, length, 0))          # tri-fan cap: fine, nothing deforms here
    last = rings[-1]
    for i in range(segs):
        bm.faces.new((last[i], last[(i + 1) % segs], tip))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob

# name: (length, radius, x offset, y offset for the knuckle arc, fan angle deg)
spec = {
    "index":  (0.072, 0.0090, -0.027, 0.004, -4),
    "middle": (0.080, 0.0092, -0.009, 0.007, -1),
    "ring":   (0.074, 0.0088,  0.009, 0.004,  2),
    "pinky":  (0.058, 0.0075,  0.027, -0.004, 5),
}
fingers = []
for n, (L, r, x, y, fan) in spec.items():
    f = make_finger(f"finger_{n}", L, r)
    f.location = (x, y, 0)
    f.rotation_euler[2] = radians(fan)          # slight outward fan
    fingers.append(f)

# Thumb: same builder, shorter, rotated out ~50 degrees at the saddle position
thumb = make_finger("finger_thumb", 0.060, 0.0105)
thumb.location = (-0.045, -0.035, -0.008)
thumb.rotation_euler = (radians(-15), radians(20), radians(-50))
fingers.append(thumb)
```

## Fusing fingers into the palm

Block the palm as a subdivided box whose leading edge has two columns per finger; open an 8-vert hole per finger (delete the two leading faces in front of each base), then bridge. `bridge_edge_loops` selects and runs fine headless in edit mode:

```python
import bpy, bmesh
from mathutils import Vector

palm = bpy.data.objects["palm"]                 # your blocked-out palm grid
for f in fingers: f.select_set(True)
palm.select_set(True)
bpy.context.view_layer.objects.active = palm
bpy.ops.object.join()

bpy.ops.object.mode_set(mode='EDIT')
def bridge_at(pt, r=0.013):
    """Select all open boundary edges near pt (finger ring + palm hole), bridge them."""
    bm = bmesh.from_edit_mesh(palm.data)        # re-fetch: bridging invalidates old bm
    bpy.ops.mesh.select_all(action='DESELECT')
    for e in bm.edges:
        if len(e.link_faces) == 1:              # boundary edge
            mid = (e.verts[0].co + e.verts[1].co) / 2
            if (mid - Vector(pt)).length < r:
                e.select = True
    bmesh.update_edit_mesh(palm.data)
    bpy.ops.mesh.bridge_edge_loops()

for n, (_L, _r, x, y, _fan) in spec.items():
    bridge_at((x, y, 0))
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.shade_smooth()
```

If any duplicate verts remain after fusing, weld them in bmesh (`bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)`). Add the webbing by selecting the lowest quad between adjacent finger bases and pulling it up slightly. Build the **left** hand only; mirror at body level (`body_anatomy`).

## Foot topology

- **Ankle: 2 full loops** where the leg meets the foot — enough for the hinge without crumpling the heel.
- **Ball of foot: 1 loop** — this is the only bend point inside a shoe, so it gets the crease loop (plus a support either side on hero assets).
- **Heel and arch**: heel is a rounded corner (a couple of loops turning under); the sole stays flat for clean ground contact, with a slight rise on the inner edge for the arch on bare feet. Shoes: flat sole, no arch.
- **Toe strategies**, cheapest first:
  1. **Shoed** — one mitten volume, no toe geometry at all (the default for game characters).
  2. **Bare, gameplay** — fused mitten toes + a separate big toe; toe creases textured.
  3. **Bare, hero closeup** — five separate toes, 2 loops per toe knuckle; only if the camera earns it.
- Feet are far cheaper than hands: a shoed game foot is often <150 tris.

The same box-blockout approach scripts well: cube scaled to 9 × 26 × 10 cm, `bmesh.ops.bisect_plane` cuts at the ball of foot, arch, and heel-front, then taper the toe box and round the heel by moving verts.

## Joint placement hints for the rig

Place these before skinning (`rigging_armatures`); the mesh loops above are built to receive them.

| Bone / joint | Place at |
|---|---|
| Wrist | on the wrist crease, centered in the volume |
| MCP / PIP / DIP knuckles | on the **center crease loop** of each 3-loop set, biased ~1/3 toward the back of the finger (the pad compresses, the back holds length) |
| Thumb CMC | inside the palm at the saddle base, near the wrist |
| Ankle | between the malleoli, ~7–8 cm up, forward of the heel's back edge |
| Ball / toe bone | at the ball-of-foot loop, just above the sole |

Bones must land on crease loops — a joint pivot between loops guarantees a mushy bend no matter how good the weights are.

## Verify

- `blender_get_viewport_screenshot` top view: knuckle line arcs, fingers fan with visible gaps, middle finger longest.
- Side view: relaxed curl visible; thumb opposes (its pad faces the fingers, not the ground).
- Curl test: in edit mode, select everything beyond one PIP crease and rotate ~90° around that loop — the crease should fold sharply while the supports keep the shaft round.
- `blender_get_object_info`: tri count vs the budget table above; all-quad in deforming zones (fingertip fans excepted).
- Feet: floor-plane check — sole flush with Z=0, no verts below ground.
- UV: one island per finger plus palm front/back for hero hands; mitten hands can share one island — see `uv_workflow`.

## Don'ts

- Don't put a single loop at a knuckle — it collapses on curl. Three (support/crease/support) or, at minimum, two.
- Don't model fingers touching or nearly touching — automatic weights bleed across and every curl drags the neighbor.
- Don't spend density in the palm center or finger shafts; it all belongs at knuckles and the thumb saddle.
- Don't leave 5-poles on top of knuckles — push them to the sides of the finger or into the palm.
- Don't build separate toes for a shoed or standard game character; it's invisible cost.
- Don't model hands flat and splayed — the relaxed curl halves the skinning correction work.
- Don't glue finger cylinders onto an unprepared palm — open matching holes and bridge so loops run wrist → fingertip.

See also: `body_anatomy`, `rigging_armatures`, `skinning_weights`, `retopology`, `lod_collision`, `uv_workflow`, `verify_loop`.
