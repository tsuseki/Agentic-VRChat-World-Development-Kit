---
title: Texel density may come from the material tiling, not the mesh UVs
topic: geometry-meshes-uvs
tags: [uv, texel-density, mainTextureScale, probuilder, tiling, primitives]
summary: Before authoring UVs to match a neighbouring surface, check whether its density comes from mesh UVs or from mainTextureScale; ProBuilder meshes carry 1 UV unit per metre and let the material supply the tiling.
---
**Symptom:** A reviewer measures a deck at 0.30 repeats/m and flags new steps at 1.5-4.3x that. Rebuilding the steps with UVs at 0.30 units/m would ship them at 0.09 repeats/m - 3.3x coarser than the defect being fixed - and since the material is shared there's no per-object correction afterwards.

**Cause:** The deck is ProBuilder with **1.0 UV unit per metre**; the 0.30 comes from `mainTextureScale = 0.30` on the shared material. Effective density = `meshUV density x mainTextureScale`.

**Fix / rule:** measure both terms on the target surface:
```csharp
// mesh-space UV units per world metre on the +Y face
for (int i = 0; i < verts.Length; i++) {
    if (normals[i].y < 0.9f) continue;
    minU = Mathf.Min(minU, uv[i].x); maxU = Mathf.Max(maxU, uv[i].x);
    minP = Mathf.Min(minP, verts[i].x * lossyScale.x); maxP = Mathf.Max(maxP, verts[i].x * lossyScale.x);
}
float meshDensity = (maxU - minU) / (maxP - minP);           // ProBuilder: 1.000
float shipped     = meshDensity * mat.mainTextureScale.x;    // what a reviewer measures
```
Then author `REP = targetShipped / mat.mainTextureScale`.

**Pitfall:** a raw `Cube` primitive with non-uniform `localScale` can never match anything: its 0..1 per-face UVs give a different density on every face (measured 0.46 / 0.35-0.60 / 0.75-1.29 repeats/m, up to 5.5x anisotropic stretch). Any scaled-primitive prop with a tiled architectural material has this defect.

Related: [authored-textures-need-aniso-8-and-trilinear](authored-textures-need-aniso-8-and-trilinear.md)
