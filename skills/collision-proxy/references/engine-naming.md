---
description: "Collision mesh naming per engine: Unreal UCX, UBX, USP and UCP prefixes, Unity colliders and Godot shapes"
metadata:
  label: "Engine Collision Naming"
---

# Engine Collision Naming

| Engine | Pattern |
|--------|---------|
| Unreal / UEFN | `UCX_SM_Name_##` convex, `UBX_` box, `USP_` sphere, `UCP_` capsule; name matches the render mesh |
| Unity | `COL_` meshes or primitives in prefab; MeshCollider Convex |
| Godot | name suffix `-colonly` (invisible), `-convcolonly` (convex), `-col` (render mesh + trimesh body) |
| Roblox | no custom meshes: MeshPart CollisionFidelity Box / Hull / PreciseConvexDecomposition |

Hull recipe and per-engine shipping: `ucx-hull-recipe.md`.
