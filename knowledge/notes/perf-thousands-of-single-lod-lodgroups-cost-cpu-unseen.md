---
title: Thousands of single-renderer LODGroups cost main-thread time even when unseen
topic: performance
tags: [LODGroup, LOD.ComputeLOD, ground cover, GPU instancing, attribution]
summary: Every LODGroup costs LOD.ComputeLOD plus renderer cull and instancing prep every frame, visible or not; merge clump populations into cells with one LODGroup each, and don't let a renderers-off sweep rank them.
---
**Symptom:** an outdoor world's worst pose paid `LOD.ComputeLOD` 1.69 ms plus ~2 ms of culling, instancing prep and
`RenderForwardOpaque.Prepare` for 33,656 GPU-instanced ground-cover prefab clumps (37k LODGroups in the scene), while
only ~41 clump draws were visible. A view with 28 clump draws paid the same ~1.5 ms.

**Cause:** Unity evaluates every active LODGroup and prepares every renderer for culling each frame on the main
thread; instancing only reduces draw submission.

**Fix / rule:** merge the clumps into cells (16 m squares, one mesh and one LODGroup per cell). `ComputeLOD` fell
1.69 → 0.19 ms and main thread 7.43 → 5.07 ms at that pose; a second world went 12,537 clumps → 142 cells,
5.54 → 4.22 ms main, 535 → 294 draws. Probe-lit clumps whose shader derives data per object need vertex-pulled cells
(see Related).

**Pitfalls:**
- Draw count is the wrong signal: after the fix draws rose 659 → 696 while main thread fell 2.36 ms.
- A renderers-off attribution sweep (`forceRenderingOff`, PerfSample `disableRootsCsv`) leaves the LODGroups
  running: `ComputeLOD` stayed at 1.73 ms, so the sweep credited the ground cover with −1.55 ms against a real −2.36 ms.
  When a root holds thousands of LODGroups, compare marker breakdowns, or sample a session with the LODGroups disabled.

**Verify:** marker breakdown (`LOD.ComputeLOD`, `Culling`) before/after, then PerfSample `mainThreadMs` in A/B/A passes.

**Related:** [perf-merging-clumps-needs-vertex-pulling-for-bundle-size](perf-merging-clumps-needs-vertex-pulling-for-bundle-size.md).
