---
description: "Tire from an ISO size code (225/45R17 -> radius, width, sidewall) in bpy: lathe profile, tread blocks by style, embossed sidewall text, hub pivot"
metadata:
  label: "Part: tire from size code"
---

# Tire from a size code

## Read the code

`225/45R17` = section width 225 mm, sidewall 45 % of the width, rim 17 in.

| Value | Formula | 225/45R17 |
|---|---|---|
| width w | 225 mm | 0.225 m |
| sidewall s | w × 0.45 | 0.101 m |
| rim radius | 17 × 0.0254 / 2 | 0.216 m |
| outer radius R | rim + s | **0.317 m** (diameter 634 mm) |

Common codes: city 195/65R15 (R 0.318), sedan 225/45R17, sport 255/35R19 (R 0.331), SUV 255/55R19 (R 0.382), truck 265/70R17 (R 0.401), kart 110/50R5 (R 0.119). Check: outer diameter within 2 % of the code.

## Build (axle on X, vehicle faces -Y, origin = hub)

```python
import bpy, bmesh, math, re
from mathutils import Vector

def tire_size(code):
    w, a, rim = re.fullmatch(r"(\d+)/(\d+)\D*(\d+(?:\.\d+)?)", code).groups()
    w = int(w) / 1000; s = w * int(a) / 100; r = float(rim) * 0.0254 / 2
    return w, s, r, r + s

def tire(code="225/45R17", blocks=64, depth=0.008):
    w, s, rim, R = tire_size(code)
    hw, rc, tw = w / 2, R - depth, 0.4 * w
    left = [(-hw*.80, rim-.004), (-hw*.86, rim+s*.1), (-hw*.96, rim+s*.3), (-hw, rim+s*.5),
            (-hw*.97, rim+s*.7), (-hw*.88, rc-s*.1), (-tw-.05*w, rc-.005)]
    crown = [(-tw + 2*tw*k/8, rc) for k in range(9)]
    prof = left + crown + [(-x, r) for x, r in reversed(left)]      # closed loop
    seg = blocks * 2
    bm = bmesh.new()
    rings = [[bm.verts.new((x, r*math.cos(2*math.pi*j/seg), r*math.sin(2*math.pi*j/seg))) for j in range(seg)] for x, r in prof]
    rows = []
    for i in range(len(prof)):
        a, b = rings[i], rings[(i+1) % len(prof)]
        rows.append([bm.faces.new((a[j], b[j], b[(j+1) % seg], a[(j+1) % seg])) for j in range(seg)])
    first = len(left)
    grooves = {2, 5}                                   # circumferential grooves of 8 columns
    tread = [rows[first+k][j] for k in range(8) if k not in grooves for j in range(seg)
             if (j + (3 <= k <= 4)) % 2 == 0]          # sport/sedan: staggered blocks
    geom = bmesh.ops.extrude_face_region(bm, geom=tread)["geom"]
    bmesh.ops.delete(bm, geom=tread, context="FACES_ONLY")   # the op keeps the originals
    for v in geom:
        if isinstance(v, bmesh.types.BMVert):
            v.co += Vector((0, v.co.y, v.co.z)).normalized() * depth
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("SM_Tire"); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new("SM_Tire", me); bpy.context.collection.objects.link(ob)
    return ob, R
```

Tread rules by style (8 crown columns, `j` = row, `k` = column):

| Style | Grooves | Block rule |
|---|---|---|
| sport / sedan | {2, 5} | `(j + (3<=k<=4)) % 2 == 0` staggered |
| suv / truck | {3, 4} | `(j + (k>=5)) % 2 == 0` chunky lugs |
| classic | {2, 5} | every row: ribs only |
| scifi | {1, 6} | centre rib solid, shoulder blocks |

## Sidewall text bump

A FONT curve (`extrude` 1.5 mm, `resolution_u` 2), converted with `bpy.data.meshes.new_from_object(ob.evaluated_get(depsgraph))`, then wrapped: each vertex `(u, v, z)` → angle `θ = θ0 - u / r_mid`, radius `r_mid + v`, x on the sidewall surface + z. `r_mid = rim + s/2`, letter height `s × 0.2`. Weld (`remove_doubles` 0.1 mm) so each letter is closed. Viewed from +X with up = +Z, `θ` decreasing reads left to right. Put two copies at 12 and 6 o'clock.

## Shading and budget

Smooth shading, 64 blocks → 128 segments ≈ 9-11k tris with text. Background cars: 32 blocks, no text (≈ 3k). The tire, rim and brake disc share the hub origin; the right side is the left wheel **turned 180° about Z**, never mirrored (text would read backwards).

**Done when:** the outer radius is within 2 % of R, every edge has two faces, and a side screenshot shows tread blocks plus readable sidewall text.

Forge: `car_part(kind=tire, tire="225/45R17")` → `r=31.7cm, tread 64, socket Hub`.

---
Sizes from the ISO metric tyre code (ETRTO). Lathe and radial-array approach adapted from Blender Agent Skills (hardsurface-modeling) by EL4CTEO, MIT licence.
