---
title: Lightmapped renderers left on BlendProbes still pay probe sampling every frame
topic: performance
tags: [lightProbeUsage, lightmapped, worker threads, probes, post-bake]
summary: Unity runs light-probe sampling for lightmapped renderers on BlendProbes every frame on worker threads; set lightProbeUsage Off on renderers that have a lightmap after every bake (pixel-identical).
---
**Symptom:** worker-thread markers `CalculateLightProbeSamplingCoordinates` + `GetLightProbeInterpolationWeights` cost
10.13 + 2.88 ms per frame at one pose of a forested world; ~10 ms in another (10.7k tree LOD renderers). Every
measured world had all lightmapped renderers on the default BlendProbes (5.5k–11k each).

**Cause:** a lightmapped renderer never reads probes in Standard-type shaders, but Unity still computes its probe
interpolation each frame.

**Fix / rule:** after every bake set `lightProbeUsage = Off` on every renderer with `0 <= lightmapIndex < 65534`.
Measured: 10,397 renderers 13.0 → 0.53 ms worker time per frame; 5,565 renderers mostly behind occlusion 0.11 ms;
5,893 renderers 0.44 ms. Pixel diffs were 0 px in every view (15, 11 and 30 views in three worlds). Template:
`.omp/skills/vrchat-world-optimization/scripts/LightmappedProbes.cs.txt`.

**Pitfalls:**
- Never apply it to probe-lit renderers: Off binds a zero SH probe there and renders them black. Re-run after each
  bake because the set of lightmapped renderers changes.
- A main-thread PerfSample shows ≤ 0.2 ms change on a 16-thread CPU; the saving is on worker threads (measure with
  all-thread recorders). [INFERENCE] On 4-core PCs those jobs compete with render jobs.
- A custom shader may read `unity_SH*` under `LIGHTMAP_ON`: prove each world with a same-camera 0-px diff.

**Verify:** all-thread marker sum before/after at the worst pose, plus the 0-px capture diff.
