---
title: Cloned pieces sharing one mesh read as a repeating pattern; offset UVs per renderer
topic: materials-textures-shaders
tags: [UV, MaterialPropertyBlock, _MainTex_ST, tiling, repetition, stair treads, texture choice]
summary: N clones sharing one mesh show the same texture patch and read as wallpaper; vary _MainTex_ST offsets per renderer, and check the texture's pattern suits the surface before retiling.
---
**Symptom:** 29 stair treads sharing one mesh all show the identical grain patch and read as a repeating chevron pattern rather than wood ("tiled plastic").

**Cause:** Usually not UV scale. Measure first: here UVs spanned u 0-3.60 over 3.60 m and v 0-0.32 over 0.32 m, perfectly isotropic. Two real faults:
1. The texture was a **herringbone parquet**, a floor pattern; on a 0.32 m tread you see one V of it on every tread. No tiling value fixes a wrong pattern; changing repeat and adding offsets made it more obviously chevron. Swap to a seamless straight-grain texture at its authored scale.
2. Every clone shows the same patch.

**Fix / rule:** Break repetition with a per-renderer `_MainTex_ST` via `MaterialPropertyBlock` (no material duplication). Standard samples `_MainTex`, `_BumpMap` and `_OcclusionMap` through `_MainTex_ST`, so albedo and relief stay registered; UV2/lightmapping is unaffected.
```csharp
var blk = new MaterialPropertyBlock(); r.GetPropertyBlock(blk);
blk.SetVector("_MainTex_ST", new Vector4(tile, tile, rng01(), rng01()));
r.SetPropertyBlock(blk);
```

**Verify:** Before tuning tiling on cloned geometry, measure `uvSpan / worldSize` on the actual face, ask whether the pattern suits the surface, and after the fix assert distinct offsets == renderer count.
