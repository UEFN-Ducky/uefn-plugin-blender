---
description: "Review renders in bpy: 8-angle turntable stills at 45 degrees framed on the bounding sphere, front/back/left/three-quarter-back views, silhouette and wireframe passes, a 128 px gameplay-size check and the fill percentage"
metadata:
  label: "Turntable and Review Views"
---

# Turntable and Review Views

| View | Camera direction (from target) | Use |
|---|---|---|
| front | -Y | proportions vs reference |
| back | +Y | backs are where AI meshes break |
| left / right | +X / -X | profile |
| three | (-1, -1, 0.6) | hero |
| three_back | (1, 1, 0.6) | back seams |
| top | +Z | layout, pivots |

Turntable: 8 stills at 45 degrees, elevation 15 degrees, orthographic or 50 mm, camera framed to the bounding sphere so the asset never changes size between frames. Render 512 px for review and once at **128 px** (gameplay size): if the silhouette doesn't read at 128 px, it won't in game. Fill under 25 % of the frame means the camera is too far.

```python
import bpy, math
from mathutils import Vector

def turntable(objs, out="//turntable_", n=8, px=512, elev=15):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    centre = sum(pts, Vector()) / len(pts)
    radius = max((p - centre).length for p in pts)
    scn = bpy.context.scene
    cam = bpy.data.objects.new("QA_Cam", bpy.data.cameras.new("QA_Cam"))
    scn.collection.objects.link(cam); scn.camera = cam
    cam.data.type, cam.data.ortho_scale = "ORTHO", radius * 2.2
    scn.render.resolution_x = scn.render.resolution_y = px
    for i in range(n):
        a = math.radians(-90 + i * 360 / n)  # frame 0 looks at the front (-Y)
        d = Vector((math.cos(a) * math.cos(math.radians(elev)), math.sin(a) * math.cos(math.radians(elev)), math.sin(math.radians(elev))))
        cam.location = centre + d * radius * 3
        cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
        scn.render.filepath = f"{out}{i * 360 // n:03d}.png"
        bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)
```

- Silhouette pass: `scn.render.film_transparent = True`, flat black emission material override (`view_layer.material_override`).
- Wireframe pass: Workbench, `shading.show_wireframes = True` or a Wireframe modifier on a copy.
- MP4 turntable: key the camera's parent empty Z rotation 0 at frame 1 and 360 at frame N+1, linear, render frames 1..N so the loop doesn't repeat a frame.

Adapted from AgentPMT Blender 3D Modeling (multi-angle renders, turntables; feature list only), ahujasid/mcp-for-blender (views; MIT) and majidmanzarpour/blender-game-skills (review views; MIT).
