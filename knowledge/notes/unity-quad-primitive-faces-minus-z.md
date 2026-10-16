---
title: Unity Quad primitive already faces -Z and has no UV2
topic: geometry-meshes-uvs
tags: [quad, primitive, normals, wall-art, single-sided, uv2]
summary: The built-in Quad has normals (0,0,-1), so rotating it 180 degrees "to face the room" hides it and whatever sits behind reads as a convincing dark panel; it also has no UV2 for lightmapping.
---
**Symptom:** Wall art built as frame box + canvas quad renders as clean dark rectangles of exactly the right size - "the painting is there but black". A TV screen quad looks black, which is even easier to mistake for correct.

**Cause:** `GameObject.CreatePrimitive(PrimitiveType.Quad)` has vertex normals `(0, 0, -1)`; at identity it already faces -Z. Rotating 180 about Y points it into the wall, and a single-sided quad seen from behind renders nothing, so the frame's front face shows through.

**Diagnose in one call:** read the material's `mainTexture` and sample the source image's mean RGB. Texture bound + image not dark + still black = facing problem, not shading.

**Fix / rule:** derive the yaw from the mesh, never hardcode it:
```csharp
var n = mf.sharedMesh.normals[0];
t.localRotation = (n.z < 0f) ? Quaternion.identity : Quaternion.Euler(0, 180f, 0); // want world -Z
```

**The Quad has no UV2** (the built-in Cube does). A ContributeGI quad without UV2 bakes garbage: either set `receiveGI = LightProbes`, or instantiate the quad mesh once, set `m.uv2 = (Vector2[])m.uv.Clone()` (UV0 is already a clean 0..1 chart), save with `AssetDatabase.CreateAsset`, and share that asset across all canvases.

Related: [door-leaf-or-canvas-hidden-inside-its-frame](door-leaf-or-canvas-hidden-inside-its-frame.md), [world-space-canvas-is-read-from-its-minus-forward-side](world-space-canvas-is-read-from-its-minus-forward-side.md)
