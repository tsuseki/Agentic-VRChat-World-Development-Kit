---
title: A copied or new outdoor scene has no occlusion data until you bake it
topic: performance
tags: [occlusion culling, Umbra, OccludeeStatic, scene copy]
summary: A world made by copying another scene ships without occlusion data; flag big scatter populations OccludeeStatic, bake, and prove it with a same-pose on/off diff.
---
**Symptom:** at spawn an outdoor world drew 3,346 batches and 4.2 M tris with `Camera.Render` 24 ms.

**Cause:** the scene (copied from a showcase scene) had never had an occlusion bake, and its 12,537 forest and grass
renderers carried no `OccludeeStatic`.

**Fix / rule:** flag the scatter renderers `OccludeeStatic` (occluders stay large opaque shell pieces) and bake
occlusion: ~30 s, 2.8 MB of data; spawn 1,851 batches, 2.0 M tris, `Camera.Render` 9.0 ms.

**Pitfalls:** one editor crashed (SIGSEGV) at occlusion-bake start on another large world; save first, and treat a
crashed bake as "no data".

**Verify:** the occlusion on/off and wide-`cullingMatrix` diffs in
`.omp/skills/vrchat-world-optimization/references/merging.md` "Occlusion"; any difference means visible things are culled.
