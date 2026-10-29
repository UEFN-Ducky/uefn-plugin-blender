# Intent first, then scale

Before the first `blender_execute_blender_code` call, write one line each. Build in this order and render the silhouette before adding any detail.

1. **Silhouette**: what reads at 20 m (a crate is a cube with a lid lip; a lamp is a pole and a head).
2. **Proportions**: height against a 1.9 m player; the 2-3 ratios that make it this object.
3. **Parts**: 3-7 pieces, biggest first.
4. **Connections**: what sits on, through or into what (bolted, welded, hinged, tied).
5. **Surface**: material and wear (painted steel, chipped at edges; oiled wood).

## Scale table (metres)

| Thing | Size |
|---|---|
| Player | 1.9 tall, 0.5 wide |
| Door opening | 1.2 W x 2.5 H (UEFN), real doors 0.9 x 2.1 |
| Ceiling | 3.0-3.84 above the floor |
| Wall / floor kit | 5.12 x 3.84 / 5.12 x 5.12, 0.2 thick |
| Stair rise / run | 0.175 / 0.28 |
| Table / chair seat | 0.75 / 0.45 |
| Crate | 0.6-1.0 |
| Barrel | 0.9 H x 0.6 across |
| Phone / mug | 0.15 / 0.10 tall |
| Car | 4.5 L x 1.8 W x 1.45 H |

Check: put a 1.9 m box next to the prop and render front and 3/4. Props that ignore player scale read as toys or monuments.

```python
import bpy
bpy.ops.mesh.primitive_cube_add(size=1, location=(-1.0, 0, 0.95)); ref = bpy.context.active_object
ref.name, ref.dimensions = "REF_Player_190cm", (0.5, 0.3, 1.9)
bpy.context.view_layer.update()
print(ref.name, tuple(round(d, 2) for d in ref.dimensions))
```

**Done when:** the render with the player box shows the prop at its table size, and the five intent lines are answered in your plan before modeling.

---
Adapted from the R2 survey (agent modeling-intent and scale conventions) and Blender Agent Skills by EL4CTEO, MIT licence.
