---
title: One mesh with garbage UV2 breaks every renderer in its Bakery lightmap group
topic: lighting-baking
tags: [Bakery, UV2, xatlas, lightmapScaleOffset, Infinity, NaN, lightmap group, GenerateSecondaryUVSet, Mesh.Clear]
summary: A single mesh with out-of-range UV2 makes Bakery's xatlas packer fail for the whole lightmap group, giving infinite lightmapScaleOffset on hundreds of renderers; assert finite offsets after every bake and scan UV2 ranges for the one culprit.
---
**Symptom:** After a bake that reported `Finished rendering` with healthy probes, ~900 renderers have `lightmapScaleOffset = (-Infinity, -Infinity, Infinity, Infinity)` (some `(-Inf,-Inf,NaN,NaN)`). `lightmapIndex` is correctly set on all of them, so an index check passes.

**Cause:** The failure is atlas-wide from a single bad mesh. Bakery's `CalculateHolderUVBounds` divides by UV extents; a mesh with garbage UV2 produced a quad ~4.3e36 tall, `xatlasAddUVMesh` failed to pack the whole atlas, `xatlasGetVertexCount` returned 0 for every holder, and the padded rect width became -Infinity for all of them. The number of broken renderers tells you nothing about how many meshes are bad: it was **one**.

Split by **lightmap group**, not hierarchy: the broken group was 100% broken while other groups were 100% clean. A clean/broken line that seems to follow scene roots can be coincidence.

How the garbage got there:
1. An FBX LOD0 imported with **no UV2** (Unity's importer unwrapper silently failed on that one mesh; `generateSecondaryUV = true` fixed LOD1/2 but not LOD0).
2. The builder fell back to `Unwrapping.GenerateSecondaryUVSet`, which **splits vertices at UV seams** (2062 in -> 2780 out), so a `src2.Length == n` guard failed.
3. The guard skipped the assignment. Because the target was a **reused mesh asset**, `Mesh.Clear()` preserved the vertex layout, so the stale UV2 channel survived, got resized with the new vertices and held uninitialized memory (values from -6.6e35 to 4.6e27).

**Fix / rule:** Always write the channel on a reused mesh asset: `outMesh.uv2 = ok ? w2 : null;`. If nothing can be folded, run `GenerateSecondaryUVSet` on the finished mesh instead.

**Verify:** After any Bakery bake, assert `lightmapScaleOffset` is **finite** on every lightmapped renderer, and in the `bakedScaleOffset` list of the `ftLightmapsStorage` on the `!ftraceLightmaps` object. When it fails, scan every lightmapped mesh's UV2 for out-of-range/NaN values and expect exactly one culprit. "Has UV2" is not the test (`uv2.Length == vertexCount` passed on all broken renderers); the range is.
