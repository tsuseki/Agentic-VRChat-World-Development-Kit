---
title: Call Physics.SyncTransforms before reading Collider.bounds or querying after a scripted move
topic: colliders-physics
tags: [physics, collider bounds, SyncTransforms, raycast, edit mode, meshcollider]
summary: Collider.bounds and physics queries see the pre-move position until Physics.SyncTransforms() runs, so a correct transform write looks like it silently failed.
---
**Symptom:** After moving colliders by script, `Collider.bounds` returns exactly the old AABB, or Raycast/OverlapCapsule in the same call report phantom hits/misses. Looks like the write failed.
**Cause:** `Physics.autoSyncTransforms` is off by default; physics picks up transform changes at the next step or query. `Collider.bounds` is served from the physics representation. `Renderer.bounds` is already correct (reads the Transform).
**Fix / rule:**
```csharp
foreach (var t in movedThings) t.localPosition = newPos;
Physics.SyncTransforms();   // required before reading bounds or raycasting in the same call
var b = col.bounds;
```
Queries in a later tool call are fine (the editor loop syncs between calls). Tell: an earlier raycast in the same script "fixes" later bounds reads.
**Related traps:**
- An inactive object has no physics representation: `Collider.bounds` reads `(0,0,0)`. Read local `BoxCollider.size` instead.
- MeshColliders on procedurally rebuilt meshes may not re-cook in edit mode (`bounds.size≈0` with `sharedMesh.vertexCount>0`; edit-mode raycasts miss them). Fix: `mc.sharedMesh = null; mc.sharedMesh = m;` then `Physics.SyncTransforms()`. Play mode/build re-cook, so only scripted verification is affected.
