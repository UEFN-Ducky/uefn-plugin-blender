# Lookdev studio (viewport)

Repeatable light + world setup so `blender_get_viewport_screenshot` always reads
form. Pair with `verify_loop`. Via `blender_execute_blender_code`.

## Why

Default gray mush hides bevels, normals, and proportion errors. Agents then
"fix" the wrong thing. Lock a **studio rig** once per session.

## Fast studio (lights)

```python
import bpy
from mathutils import Euler
import math

# Clean old studio helpers (optional — only if you named them)
for name in list(bpy.data.objects.keys()):
    if name.startswith("LGT_Studio_"):
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)

def add_area(name, loc, rot_deg, energy, size=5.0):
    bpy.ops.object.light_add(type='AREA', location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.data.energy = energy
    ob.data.size = size
    ob.rotation_euler = Euler([math.radians(a) for a in rot_deg], 'XYZ')
    return ob

add_area("LGT_Studio_Key", (3, -3, 4), (50, 0, 40), 400, 4)
add_area("LGT_Studio_Fill", (-3, -2, 2), (60, 0, -40), 120, 6)
add_area("LGT_Studio_Rim", (0, 4, 3), (50, 0, 180), 200, 3)
```

Tune energies if the mesh is tiny/huge — form should show **chamfer highlights**
without clipping to white.

## World / HDRI (optional)

```python
import bpy
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
nt = world.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputWorld")
bg = nt.nodes.new("ShaderNodeBackground")
bg.inputs["Strength"].default_value = 0.4
nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
# Optional: Environment Texture → Background Color for HDRI lookdev
```

Keep Strength modest so Material Preview isn't blown out.

## Viewport for screenshots

```python
import bpy

def view3d():
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            return area.spaces.active
    raise RuntimeError("No VIEW_3D")

sh = view3d().shading
sh.type = 'SOLID'
sh.light = 'STUDIO'          # or MATCAP for pure form
sh.studio_light = 'basic_1.exr'
sh.use_scene_lights = True   # see LGT_Studio_* in Material/Rendered
sh.use_scene_world = False
```

| Pass | Shading |
|------|---------|
| Silhouette / proportion | SOLID + FLAT or MATCAP single color |
| Bevels / panels | SOLID + cavity / studio lights |
| Albedo / roughness | MATERIAL |
| Final lookdev | RENDERED (EEVEE) with studio lights |

Full mode table: `verify_loop`.

## Camera / framing

- ¾ view for props; orthographic front/side for proportion locks (`reference_match`).
- Frame the 1.8 m scale ref in-shot when unsure (`scale_library`).
- Turntable: rotate empty parent or orbit; same FOV each compare.

## Don'ts

- Don't judge materials under pure flat gray with no key light.
- Don't leave 10 random suns from prior tests — name `LGT_Studio_*` and reuse.
- Don't skip a screenshot after "one more bevel."

Next: `verify_loop` every change → discipline skill → `asset_qa`.
