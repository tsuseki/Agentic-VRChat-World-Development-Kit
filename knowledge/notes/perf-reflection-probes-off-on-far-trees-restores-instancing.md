---
title: Different reflection probes break tree instancing; turn them off beyond the walk zone
topic: performance
tags: [reflection probes, GPU instancing, trees, draw calls]
summary: Trees blended by different reflection probes can't instance together; set reflectionProbeUsage Off on tree groups ~30 m beyond every walk-zone eye point and keep probes on inside it.
---
**Symptom:** one forest pose drew 1,116 draws although every tree used one instanced material.

**Cause:** renderers blended by different reflection probes go into separate instancing batches.

**Fix / rule:** a scene override `reflectionProbeUsage = Off` on tree groups farther than ~30 m horizontally from every
walk-zone eye point (3,096 groups, 9,288 renderers): 1,116 → 787 draws. Probes Off on every tree made the woods 16 %
brighter and was rejected, so keep them On inside the walk zone. Keep a rollback function.

**Pitfalls:** far shaded conifers get slightly lighter (px > 18: 0.000–0.001 %; px > 6: 0.92 % at one pose; 0 px
inside the woods). Re-check the far trees after the woods' probes are re-baked.

**Verify:** draws at the forest poses, same-camera diff with a > 6 threshold as well as > 18.
