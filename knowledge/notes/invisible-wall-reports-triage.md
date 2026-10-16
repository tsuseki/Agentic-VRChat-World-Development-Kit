---
title: Triage 'invisible wall' reports: jump impulse first, then a capsule sweep
topic: colliders-physics
tags: [invisible wall, jump, PlayerModSetter, collider bounds, OverlapCapsule, sweep]
summary: VRChat's default jump impulse is 0, which makes kerbs and small props feel like invisible walls; rotated thin box colliders also look like huge slabs if you read Collider.bounds.
---
**Symptom:** Testers report invisible walls / being unable to get past edges.
**Causes and fixes:**
- **No jump:** a world that never calls `SetJumpImpulse` has no jump, so every kerb, 0.8 m prop or steep slope blocks on foot. Add the SDK's `Assets/UdonSharp/UtilityScripts/PlayerModSetter.cs` (defaults jump 3, run 4, walk 2, strafe 2, gravity 1; destroys itself after `Start`). Check this first.
- **Misread colliders:** `Collider.bounds` is a world AABB; a 0.6 × 1.1 × 22 m barrier laid diagonally reports (8.9, 3.2, 22.8). Use `Vector3.Scale(col.size, transform.lossyScale)` for true extents and sample the footprint in local space against nearby visible geometry.
**Verify (prove no invisible wall):** raycast down on a grid over the map, place a player capsule (r 0.35, 0.05→1.8 m above the hit) at each cell, `Physics.OverlapCapsule` ignoring triggers and terrain; group hits by GameObject. A hit cell with no visible prop within ~3.5 m is a real invisible wall. 218k cells ran in seconds; cache mesh data before the loop — `mesh.colors`/`mesh.triangles` allocate per call and stall the editor.
