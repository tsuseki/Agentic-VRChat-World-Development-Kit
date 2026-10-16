---
title: 'Overlapping lightmap UVs' on ProBuilder meshes is usually a gutter-in-texels problem
topic: lighting-baking
tags: [lightmap UV, UV2, ProBuilder, packMargin, lightmapPadding, scaleInLightmap, black prop, texel density]
summary: ProBuilder's UV2 pack margin is a UV-space constant while Unity's padding is in texels, so islands bleed and props bake black; measure the gap in texels, widen packMargin until it clears padding+1, then trim scaleInLightmap back.
---
**Symptom:** Unity warns "overlapping lightmap UVs, N texels" on ProBuilder geometry, and some props bake **pure black**. Pairwise testing of UV2 islands shows zero actual overlaps.

**Cause:** ProBuilder packs UV2 with `unwrapParameters.packMargin = 20` = **0.02 UV units** (UV-space). Unity dilates every chart by `lightmapPadding` = **4 texels** (texel-space). On ordinary props 0.02 UV lands at only 1.1-2.0 texels, so islands bleed. The island that bleeds in is usually the one facing away from light (a bench underside, a door edge against a wall), which bakes near zero and floods the visible face; hence black, not blotchy.

**Diagnose** (charts = connected components of the triangle-vertex graph; union-find over `mesh.triangles`, since UV seams duplicate vertices):

```
metresPerUV = sqrt(sum(world tri area) / sum(uv2 tri area))
T           = lightmapResolution * scaleInLightmap * metresPerUV
gapTexels   = (min gap between chart AABBs in UV) * T      // flag if < padding + 1
```

**Fix / rule:**
1. Widen the gutter, don't re-unwrap blind. Texel density (`resolution * scaleInLightmap`) is independent of `packMargin` (a bigger margin shrinks islands but grows `metresPerUV` identically), so a wider gutter costs atlas area only, ~1.2x. Iterate `UnwrapParam.packMargin` via `Unwrapping.GenerateSecondaryUVSet` until `gapTexels >= padding + 1`; one pass converged every time at 0.054-0.080. Write `pm * 1000` back into `ProBuilderMesh.unwrapParameters.packMargin`, or a later ProBuilder regeneration silently reintroduces the bug.
2. Then trim scale back. A blunt `scaleInLightmap *= 2.5` on offenders also clears the warning but took atlas demand from ~8 to 19.17 Mtexel. For every lightmapped renderer solve the smallest scale that still holds the gutter:

```csharp
float needed = 6f / (res * metresPerUV * minGapUV);   // 6 texels = padding + 2 headroom
float ns = Mathf.Clamp(needed, 1.0f, currentScale);   // never raise, never go under 1.0
```

That trimmed 165 objects, 19.17 -> 13.77 Mtexel, worst gutter still 5.03 texels.

**Scope / guards:** this fix is for renderers of ~1.3 m largest dimension and up; anything smaller goes to light probes first ([probe-light-small-objects-instead-of-lightmapping](probe-light-small-objects-instead-of-lightmapping.md)). Even on larger renderers, if the middle dimension is under ~0.12 m or `T < 12`, no margin helps; probe-light those too. Check `T` for absurd atlas claims first: two 60 m x 0.05 m skirtings each demanded a 2970-texel region against a 2048 atlas, starving everything else.

**Verify:** Measure `gapTexels` across **every** lightmapped renderer, not just those named (the console named 98, measurement found 261), and re-run the sweep after fixing instead of trusting the algebra.
