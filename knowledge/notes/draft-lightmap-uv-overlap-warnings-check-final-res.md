---
title: Lightmap UV overlap warnings at draft resolution may be harmless; check crops at final resolution first
topic: lighting-baking
tags: [lightmap UV, UV2, overlap warning, draft bake, trees, Smart UV, scaleInLightmap]
summary: Draft bakes warned of overlapping lightmap UVs on almost every renderer (Smart-UV trees with margin 0.01 and generated walls alike), yet the final-resolution bake with 3× lightmap scale on near trees showed no blotches or bleeding; inspect final-res crops before changing UV2 margins.
---
**Symptom:** A low-resolution draft bake reported "overlapping lightmap UVs" on almost every renderer: Blender-built trees with Smart UV Project margin 0.01 and script-generated walls alike.

**Cause:** The warning is computed in texels at the bake's resolution; at draft texel density the gutters are under the padding, so nearly everything trips it. At final resolution (and 3× scale in lightmap for near trees) the same UV2 margins span enough texels.

**Fix / rule:** Don't re-unwrap or widen UV2 margins on the draft warning alone. Bake at final resolution, then inspect crops of the warned renderers for blotches and bleeding; fix only what actually shows (see [overlapping-lightmap-uv-warning-is-a-gutter-problem](overlapping-lightmap-uv-warning-is-a-gutter-problem.md) for measuring gutters in texels when it does).

**Verify:** final-resolution crops of the flagged renderers (near trees, wall seams) show no dark/bright island bleed; gutter in texels ≥ padding + 1 on the ones that matter.
