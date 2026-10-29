---
description: "Modular weapon part kit (receiver, barrel, handguard, stock, grip, mag, sights, muzzle), part naming and pivots, moving parts, plus origin, forward axis and sockets per engine (UE5/UEFN, Unity, Godot)"
metadata:
  label: "Weapon parts, origin and sockets"
---

# Modular weapon kit, origin and sockets

## Part kit

Each part is its own object with its pivot at the point where it attaches, so parts swap like real ones. Name them `SM_WPN_<Weapon>_<Part>`.

| part | attaches at (pivot) | variants | moves? |
|---|---|---|---|
| receiver (upper + lower) | grip origin | std, bullpup, sci-fi | no (it is the root) |
| barrel | receiver front, bore axis | 25 / 37 / 41 / 51 cm | no |
| handguard | receiver front | quad rail, M-LOK tube, wood | no |
| stock | receiver rear, bore axis | fixed, collapsible, skeleton, precision, none | collapsible slides |
| grip | grip origin | 18° / 22° / 25° | no |
| magazine | top of the mag well | std, extended (x1.6), drum, tube | yes: reload |
| sight / optic | rail top, at the sight line | iron, red dot, holo, 4x / 24x scope | no |
| muzzle | barrel end | flash hider, brake, suppressor (x3-4 bore length) | no |
| slide / bolt / charging handle | rest position | | yes: fire, reload |
| trigger, hammer, safety | hinge pin | | yes: rotate |

Rules: the bore axis is one straight line through barrel, muzzle and handguard centres; put a `SOCKET_` empty at each attach point so parts snap; keep moving parts separate down to export (UE skeletal weapon) or joined (static prop).

```python
import bpy
def snap(part, socket):
    """Move part so its origin sits on the socket empty of the base weapon."""
    part.matrix_world.translation = bpy.data.objects[socket].matrix_world.translation
snap(bpy.data.objects["SM_WPN_Rifle_Muzzle_Suppressor"], "SOCKET_Muzzle")
```

## Sockets (all engines)

| socket | where | used for |
|---|---|---|
| `Grip` | main-hand grip, = origin | attach to hand_r |
| `Muzzle` | barrel exit, on the bore axis, facing forward | flash, tracer, projectile spawn |
| `Sight` | rear sight / optic eye line | ADS camera |
| `Magazine` | mag well | reload VFX, mag swap |
| `Shell` | ejection port, facing right | casing eject |
| `OffHand` | handguard where the support hand sits | left-hand IK |
| melee `TrailBase` / `TrailTip` | blade base and tip on the edge | swing trail |

## Origin and axis per engine

| engine | units | up / forward | origin | sockets | Blender export |
|---|---|---|---|---|---|
| UE5 / UEFN | cm | Z up, muzzle +X | top of the pistol grip / main-hand grip | empties named `SOCKET_Muzzle` etc., parented to the mesh: the FBX importer turns them into Static Mesh sockets | muzzle at Blender +X; FBX scale 1.0 with Apply Unit on; default axes (Forward -Z, Up Y) keep Blender +X as UE +X |
| Unity | m | Y up, muzzle +Z | grip | child empties (become Transforms) named `Muzzle` etc. | muzzle at Blender -Y; FBX Forward -Z, Up Y, Apply Transform on |
| Godot 4 | m | Y up, muzzle -Z | grip | empties become `Node3D`s | muzzle at Blender +Y; glTF, +Y Up on |

UEFN note: custom meshes ship as props, pickups, display or Scene Graph entities (Fortnite weapon items keep their own meshes), so the same origin and sockets let you line them up with a hand or a mount.

```python
import bpy
def add_socket(mesh, name, loc_cm):
    e = bpy.data.objects.new("SOCKET_" + name, None)
    e.empty_display_type, e.empty_display_size = "ARROWS", 0.03
    bpy.context.collection.objects.link(e)
    e.parent, e.location = mesh, [v / 100 for v in loc_cm]
gun = bpy.data.objects["SM_WPN_Rifle"]
for n, p in {"Muzzle": (58, 0, 7.2), "Sight": (-2, 0, 13), "Magazine": (12, 0, -2)}.items():
    add_socket(gun, n, p)
```

Done when: the origin is at the grip (`gun.location` reads 0 after `Apply > All Transforms`), the muzzle points down the engine's forward axis, and each socket empty sits on its part in a side render.

## Forge path

One call builds the kit already joined, origin at the grip, sockets on the node: `{"tool": "forge_hq", "op": "weapon", "params": {"kind": "rifle", "parts": {"stock": "skeleton", "sight": "holo", "muzzle": "brake", "mag": "extended"}}}`.

---
Part breakdown adapted from Blender Agent Skills (hardsurface-modeling) by EL4CTEO, MIT licence. Axis conventions are from the Unreal, Unity and Godot import documentation.
