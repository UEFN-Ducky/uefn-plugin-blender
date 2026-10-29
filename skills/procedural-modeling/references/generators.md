# Generators: buildings, kits, stairs, fences, pipes, cables

Each function builds one closed `SM_` mesh in metres. UEFN grid: walls 5.12 x 3.84 m, floors 5.12 x 5.12 m, pivot on the min corner so pieces snap.

```python
import bpy, bmesh
from mathutils import Matrix, Vector

def _obj(bm, name):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); return ob

def _boxes(specs):  # [((w, d, h), (x, y, z) centre)]
    bm = bmesh.new()
    for dims, at in specs:
        bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation(at) @ Matrix.Diagonal((*dims, 1)))
    return bm

def _cut(ob, specs, op="DIFFERENCE"):
    c = _obj(_boxes(specs), "cut")
    m = ob.modifiers.new("b", "BOOLEAN"); m.operation, m.solver, m.object, m.use_self = op, "EXACT", c, True
    with bpy.context.temp_override(object=ob, active_object=ob):
        bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(c)

def tris(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)

def kit_wall(w=5.12, h=3.84, t=0.2, opening="door"):
    ob = _obj(_boxes([((w, t, h), (w / 2, t / 2, h / 2))]), "SM_Wall")
    if opening == "door":
        _cut(ob, [((1.0, t * 3, 2.2), (w / 2, t / 2, 1.1))])
    elif opening == "window":
        _cut(ob, [((1.2, t * 3, 1.2), (w / 2, t / 2, 1.5))])
    return ob

def kit_floor(w=5.12, d=5.12, t=0.2):
    return _obj(_boxes([((w, d, t), (w / 2, d / 2, -t / 2))]), "SM_Floor")

def building(floors=6, w=10.0, d=8.0, fh=3.0, bay=3.0):
    h = fh * floors
    ob = _obj(_boxes([((w, d, h), (0, 0, h / 2))]), "SM_Building")
    if floors > 1:  # 15 cm ledge at each floor line
        _cut(ob, [((w + .2, d + .2, .15), (0, 0, fh * f)) for f in range(1, floors)], "UNION")
    wins = []
    for f in range(floors):
        z = fh * f + fh * 0.55
        for length, along_x, half in ((w, True, d / 2), (d, False, w / 2)):
            cols = max(1, int(length // bay))
            for c in range(cols):
                s = -length / 2 + length / cols * (c + .5)
                for side in (-1, 1):  # windows 1.2 x 1.5 m, 15 cm deep
                    wins.append(((1.2, .3, 1.5), (s, side * half, z)) if along_x else ((.3, 1.2, 1.5), (side * half, s, z)))
    wins.append(((w - .6, d - .6, .8), (0, 0, h)))  # roof well behind a 30 cm parapet
    _cut(ob, wins)
    return ob

def stairs(n=12, width=1.0, rise=0.175, run=0.28):
    prof = [(0, 0), (n * run, 0)]
    for i in reversed(range(n)):
        prof += [((i + 1) * run, (i + 1) * rise), (i * run, (i + 1) * rise)]
    bm = bmesh.new(); f = bm.faces.new([bm.verts.new((x, 0, z)) for x, z in prof])
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, vec=(0, width, 0), verts=[e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return _obj(bm, "SM_Stairs")

def fence(length=4.0, h=1.0, spacing=1.0):
    posts = max(2, round(length / spacing) + 1)
    specs = [((.1, .1, h), (length * i / (posts - 1), 0, h / 2)) for i in range(posts)]
    specs += [((length, .04, .08), (length / 2, 0, z)) for z in (h * .35, h * .8)]
    return _obj(_boxes(specs), "SM_Fence")  # separate closed shells: no union needed

def tube(path, radius=0.05, sag=0.0, name="SM_Pipe"):
    pts = [Vector(p) for p in path]
    if sag:  # hanging cable: parabola, 8 points per span
        pts = [a.lerp(b, t / 8) - Vector((0, 0, sag * 4 * (t / 8) * (1 - t / 8))) for a, b in zip(pts, pts[1:]) for t in range(8)] + [pts[-1]]
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for pt, co in zip(sp.points, pts):
        pt.co = (*co, 1)
    cu.bevel_depth, cu.bevel_resolution, cu.use_fill_caps = radius, 2, True
    tmp = bpy.data.objects.new(name, cu); bpy.context.scene.collection.objects.link(tmp)
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(tmp); ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    return ob

for ob in (building(6), kit_wall(), kit_floor(), stairs(), fence(), tube([(0, 0, 3), (5, 0, 3)], 0.02, 0.4, "SM_Cable")):
    print(ob.name, tris(ob))
```

Reference results: building 6 floors 1192 tris, wall with door 28 tris, floor 12, stairs 100, fence 84, cable 140.

**Done when:** a front and top render shows rows of recessed windows, a parapet, stairs with even treads and the cable sagging between its ends; kit pieces snap edge to edge on the 5.12 m grid.

---
Adapted from Blender Agent Skills (procedural / geometry-nodes) by EL4CTEO, MIT licence. Same generators as Forge `procedural(kind=...)`.
