---
title: "Bad textures" on a hand-built mesh is usually material tiling anisotropy; fix it in UV1
topic: geometry-meshes-uvs
tags: [tiling, UV, box projection, anisotropy, shared material, repeats per metre]
summary: Measure effective repeats per metre per axis (mesh UV per metre x material tiling); fix anisotropy with a per-axis world box projection in UV1, leaving shared materials and UV2 untouched.
---
**Symptom:** A procedurally built prop (e.g. a bar counter) is reported as having "bad textures". The texture and mesh UVs are fine.

**Cause:** The shared material is tiled anisotropically, e.g. `(11.20, 2.13)`, a 5.3x ratio, so wood runs as a smear one way and postage stamps the other. A uniformly wrong scale looks cheap; anisotropy looks broken.

**Fix / rule:** The number that matters is **effective repeats per metre = (mesh UV per metre) x (material tiling), per axis**. Around 0.5-1.0 repeats/m reads correctly for wood/plaster at arm's length. Do not edit the shared material (its values suit the rest of the set); write a world-space box projection into UV1 with a per-axis scale that cancels the material's anisotropy:
```csharp
// per vertex, pick the axis by the dominant component of the WORLD normal
// |n.y| -> uv = (wx*ku, wz*kv)   |n.x| -> (wz*ku, wy*kv)   else -> (wx*ku, wy*kv)
m.uv = uv;  m.RecalculateTangents();  m.RecalculateBounds();
// ku/kv so tiling*k hits the target, e.g. tiling (11.20, 2.13) -> ku 0.0446, kv 0.2347 => 0.50 both ways
```
Save as a new `.asset` next to the original (`Foo_boxuv.asset`) and swap the MeshFilter so the generator stays reproducible.

**Pitfalls:**
- Copy UV2 through verbatim; rewriting it re-lays the lightmap and in a Bakery scene can poison the atlas.
- Normal-based axis selection only works on hard-split meshes (a box with 24 verts). On smooth-shaded meshes use per-triangle normals and split vertices there.
- `RecalculateTangents` is mandatory (see [generated-mesh-needs-recalculatetangents](generated-mesh-needs-recalculatetangents.md)).

**Verify:** On any "textures look wrong" report for a procedural mesh, print effective repeats/m per axis for every material before opening the texture or UV editor.

Related: [uv-density-may-live-in-the-material](uv-density-may-live-in-the-material.md), [solve-uv-scale-from-mesh-triangles](solve-uv-scale-from-mesh-triangles.md).
