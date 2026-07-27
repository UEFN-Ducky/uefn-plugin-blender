# Geometry Nodes

Procedural arrays, scatter, and generators **inside Blender**. UEFN does not run GN graphs — realize → mesh → export. Name groups `GN_*`. Via `blender_execute_blender_code`.

## When

- Bolt / rivet arrays, fence posts, railing repeats
- Gravel / debris scatter for lookdev
- Parametric trim / panel generators before freeze

Not for: final character topology, live foliage systems in UEFN (export baked clusters).

## Minimal modifier + group

```python
import bpy
ob = bpy.data.objects["SM_Panel"]
mod = ob.modifiers.new("GN_Array", 'NODES')
# Assign an existing node group or build one:
ng = bpy.data.node_groups.get("GN_GridArray")
if ng:
    mod.node_group = ng
```

Building a tiny grid array in code (Blender 4.x node API):

```python
import bpy
ng = bpy.data.node_groups.new("GN_GridArray", 'GeometryNodeTree')
# Blender 4+: interface sockets
ng.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
ng.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
nodes, links = ng.nodes, ng.links
nin = nodes.new("NodeGroupInput"); nin.location = (-400, 0)
nout = nodes.new("NodeGroupOutput"); nout.location = (400, 0)
# Prefer authoring complex graphs in the editor; keep agents on realize/export path
links.new(nin.outputs[0], nout.inputs[0])
```

For agent workflows: reuse pre-authored `GN_*` groups in the `.blend`; don't invent 40-node trees from scratch mid-task.

## Realize before export

```python
import bpy
ob = bpy.data.objects["SM_ScatterHost"]
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
# Make instances real
bpy.ops.object.duplicates_make_real()
# Or: apply GN modifier
with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob]):
    for mod in list(ob.modifiers):
        if mod.type == 'NODES':
            bpy.ops.object.modifier_apply(modifier=mod.name)
# Join if many pieces
# bpy.ops.object.join()
```

Then `mesh_cleanup`, name `SM_*`, purge helpers.

## Scatter discipline

- Cap instance counts before realize (hundreds, not hundreds of thousands).
- Seed randomness for repeatable looks.
- Origin of instances: ground contact for plants (`vegetation`).
- Keep scatter lookdev separate from the export collection (`scene_organization`).

## Don'ts

- Don't expect Geometry Nodes to run in UEFN.
- Don't realize 50k instances into one mesh without LOD plan (`lod_collision`).
- Don't leave unrealized GN as the only copy of hero geometry.

Next: `mesh_cleanup` → `asset_qa` → `uefn_export`.
