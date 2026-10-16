---
title: Check procedural mesh winding against a primitive Cube; confirm by render
topic: geometry-meshes-uvs
tags: [procedural mesh, winding, normals, backface culling, inside-out]
summary: Compare each triangle's geometric normal with its stored vertex normals; a primitive Cube scores 12/12, a hand-built mesh scoring 0/N is inverted — but the test misreports imported FBX meshes.
---
**Symptom:** A script-built box looks roughly right but you can see into it from some angles — outer faces that should occlude are culled.
**Fix / rule:**
```csharp
var geo = Vector3.Cross(v[t[i+1]] - v[t[i]], v[t[i+2]] - v[t[i]]).normalized;
var stored = (n[t[i]] + n[t[i+1]] + n[t[i+2]]).normalized;
bool agrees = Vector3.Dot(geo, stored) > 0f;
```
- Ground-truth against `GameObject.CreatePrimitive(PrimitiveType.Cube)` (12/12 agree). A generated mesh at 0/N is inverted: swap `t[i+1] <-> t[i+2]` per triangle, keep normals, `RecalculateTangents`, regenerate UV2.
- Rebuild in place with `mesh.Clear()` on the existing `.asset` so MeshFilter references survive.
**Pitfalls:** The test also reports "disagree" on correct imported FBX meshes; it is conclusive only for meshes you generated. For imports, the render is the oracle.
**Verify:** One 3/4 render where an outer face must occlude interior contents.
