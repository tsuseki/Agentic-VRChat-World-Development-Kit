---
title: Seat complex prefabs by downward raycast, not by bounds — and get the ray off your own collider
topic: placement-layout-design
tags: [seating, raycast, bounds, SkinnedMeshRenderer, vehicle, Physics.SyncTransforms, reseat]
summary: Prefabs with UI/cameras at the origin or unposed skinned meshes have junk bounds; raycast the ground with the object's own colliders disabled, and seat from bounds.min only on simple props.
---
**Symptom:** parked vehicles or props float or sink after scripted placement; or bar stools end up standing on the counter.

**Scope:** the raycast here is for seating bundle prefabs on ground whose collider *is* the visible surface (terrain, road, floor mesh collider). Where the walkable collider is a separate flat proxy, seat to the visible mesh instead (see the visible-floor note); and to *audit* seating in a collider-free prop world, compare renderer bounds, not rays.

**Cause / rules:**
- Bundle prefabs (vehicle + race system + cameras + UI at the origin) have bounds spanning the whole map. Don't seat them from bounds; raycast.
- `GetComponentsInChildren<Renderer>()` pulls in SkinnedMeshRenderers whose bounds on an unposed rig are junk. Filter to `MeshRenderer`s with meaningful size (e.g. `mesh.bounds` max-dim ≥ 0.25 m) and within ~15 m of the root.
- The downward ray **hits the object's own collider** and reports ground too high: `SetActive(false)` + `Physics.SyncTransforms()` before the raycast, then re-enable.
- Check where the root pivot is: many vehicle rigs put it exactly at the wheel contact patch, so `root.y = ground.y`.
- Rays cast at old blockout positions can hit furniture: stools placed by raycasting at the old XZ (which was over the counter) stood on the counter top. Place seating on a ring **outside** the counter perimeter (e.g. 0.62 m out from each face, facing inward), seated on the floor.
- Simple props sunk into or floating above the floor: `pos.y += floorHit.y − renderer.bounds.min.y`. Mind base pivots (seat at floor + 5 mm, not floor + halfHeight).
- Cloning props without import-scale guesswork: `Instantiate` an existing correctly placed scene prop, parent under a unit-scale group, `localScale = src.lossyScale`, compose yaw with its rotation, seat by `bounds.min.y`.

See also [seat-props-on-visible-floor-not-collider-proxy](seat-props-on-visible-floor-not-collider-proxy.md), [compose-fbx-root-rotation-never-assign](compose-fbx-root-rotation-never-assign.md).
