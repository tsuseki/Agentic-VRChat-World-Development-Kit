---
title: Hand-rolled mesh builders can wind triangles against their normals — make them self-correcting
topic: geometry-meshes-uvs
tags: [mesh generation, procedural mesh, winding order, normals, backface culling, inside-out]
summary: A scripted box/quad helper can emit every triangle inside-out while normals look correct; test winding against a primitive Cube control and make the builder flip inverted pairs itself — the test misreports imported FBX meshes.
---
**Symptom:** Scripted boxes (steps, benches, podium) look missing or very dark in an unbaked scene, or you can see into them from some angles; it survives a fix round as a "lighting/probe problem". Measured: 12 of 12 triangles per mesh wound opposite the stored normal.

**Cause:** The builder's corner order winds triangles inward. Normals are unit-length and outward, so a normals check passes. With backface culling the object is see-through from outside, solid from inside. No console warning.

**Check — geometric winding vs stored normal per triangle:**
```csharp
var a=v[tr[i]]; var b=v[tr[i+1]]; var c=v[tr[i+2]];
var geo = Vector3.Cross(b-a, c-a);
var stored = n[tr[i]] + n[tr[i+1]] + n[tr[i+2]];
bool inverted = Vector3.Dot(geo, stored) < 0;
```
Report `inverted/total`. Ground-truth against `GameObject.CreatePrimitive(PrimitiveType.Cube)`: it must read 0/12 inverted. A generated mesh at N/N is fully inverted.

**Fix / rule:** don't just swap the winding in the builder (moves the bug). Make it **self-correcting**: after emitting each quad, compute the dot and flip that triangle pair (`t[i+1] <-> t[i+2]`, keep normals) if negative, logging an `auto-flipped N` count. Then later edits to corner order can't produce inverted meshes. To repair an existing mesh, flip, `RecalculateTangents`, regenerate UV2, and save it as a **new** asset (`AssetDatabase.CreateAsset`) assigned to the MeshFilter; rewriting the existing asset in place can leave the renderer drawing the old mesh (see [copyserialized-into-existing-mesh-renders-stale](copyserialized-into-existing-mesh-renders-stale.md)).

**Pitfalls:** The test also reports "disagree" on correct imported FBX meshes; it is conclusive only for meshes you generated. For imports, the render is the oracle. One facing test covers only one section; see [prove-winding-per-mesh-section](prove-winding-per-mesh-section.md).

**Verify:** One 3/4 render where an outer face must occlude interior contents.
