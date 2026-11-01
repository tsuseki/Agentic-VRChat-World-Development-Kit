---
title: Static batching on instanced LODGroup trees bloats the upload; clear BatchingStatic
topic: performance
tags: [BatchingStatic, static batching, GPU instancing, LODGroup, bundle size]
summary: BatchingStatic on LODGroup tree and plant renderers stores combined copies of LOD0 geometry in the build; clear it on instanced foliage and let GPU instancing batch (no rebake).
---
**Symptom:** a planted world built at 394.8 MB; its scene held 469 MB of uncompressed static-batch combined meshes
(one forest root 351 MB, trees 114 MB). Another went 1,595.7 MB raw before the fix.

**Cause:** static batching bakes a transformed copy of every flagged renderer's mesh into combined meshes stored with
the scene, so thousands of tree instances become thousands of geometry copies. It also prevents GPU instancing on
those renderers (choose one per asset).

**Fix / rule:** clear `BatchingStatic` on LODGroup tree and plant renderers whose shader is instanced. Results:
5,281 renderers 394.8 → 168.2 MB with draws at spawn 622 → 340 and render time unchanged; 5,640 renderers
396.6 → 142.4 MB (with the world's own bake); 1,595.7 → 286.9 MB raw with ≤ 0.033 % pixels changed; one forest
7,123 → 1,248 draws. BatchingStatic is not a lightmap input, so no rebake; instancing still batches lightmapped trees
after a bake when they share a lightmap index (394 vs 336 draws).

**Pitfalls:**
- Detect it by scene file size or the build report, never triangle counts. In play mode `UnityStats` tris on statically
  batched props are combined-mesh counts.
- Static batching happens at build or play time, so the pixel proof must be a play-mode diff; edit-mode renders can't differ.

**Verify:** scene-bundle size A/B, play-mode draws and `mainThreadMs` at the same poses, play-mode capture diff.
