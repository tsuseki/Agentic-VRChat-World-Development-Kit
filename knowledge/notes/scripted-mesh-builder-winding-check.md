---
title: Hand-rolled mesh builders can wind triangles against their normals — make them self-correcting
topic: geometry-meshes-uvs
tags: [mesh generation, winding order, normals, backface culling, inside-out]
summary: A scripted box/quad helper can emit every triangle inside-out while normals look correct; the object is see-through from outside and gets misdiagnosed as a lighting problem.
---
**Symptom:** Scripted boxes (steps, benches, podium) look missing or very dark in an unbaked scene; it survives a fix round as a "lighting/probe problem". Measured: 12 of 12 triangles per mesh wound opposite the stored normal.

**Cause:** The builder's corner order winds triangles inward. Normals are unit-length and outward, so a normals check passes. With backface culling the object is see-through from outside, solid from inside. No console warning.

**Check — geometric winding vs stored normal per triangle:**
```csharp
var a=v[tr[i]]; var b=v[tr[i+1]]; var c=v[tr[i+2]];
var geo = Vector3.Cross(b-a, c-a);
bool inverted = Vector3.Dot(geo, nz[tr[i]]) < 0;
```
Report `inverted/total`; a known-good control must read 0/12.

**Fix / rule:** don't just swap the winding in the builder (moves the bug). Make it **self-correcting**: after emitting each quad, compute the dot and flip that triangle pair if negative, logging an `auto-flipped N` count. Then later edits to corner order can't produce inverted meshes.
