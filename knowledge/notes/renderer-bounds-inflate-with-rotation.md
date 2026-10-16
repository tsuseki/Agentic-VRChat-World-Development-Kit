---
title: Renderer.bounds inflates for rotated objects — measure size from the mesh
topic: unity-editor-scripting-mcp
tags: [Renderer.bounds, AABB, rotation, mesh bounds, clash test, placement solver]
summary: Renderer.bounds is the world-axis-aligned box of the rotated local bounds, so a yawed prop measures up to 1.41x too wide, faking distortion, overhang and clash failures.
---
**Symptom:** Randomly yawed bowls on consoles are reported as distorted (native w/h 2.79, placed 3.94); props "hang off" surfaces they sit inside; a placement solver oscillates for 40 iterations between separation and footprint clamping.

**Cause:** `Renderer.bounds` is world-axis-aligned, computed from the local AABB after rotation. At 45° yaw horizontal extent inflates by √2 = 1.41×:
```
0.46 (native w) * 0.70 (scale) = 0.322 m   <- truth
measured renderer.bounds width  = 0.453 m  <- 0.322 * 1.41
```

**Fix / rule:** measure size from the mesh:
```csharp
var nb = mf.sharedMesh.bounds.size;      // local, rotation-free
var s  = t.lossyScale;
float trueW = nb.x * s.x, trueH = nb.y * s.y;
```
Use `Renderer.bounds` only as a conservative pre-filter for overhang, clash and clearance tests; confirm real hits with mesh bounds, an OBB, or a collider test before moving anything.
