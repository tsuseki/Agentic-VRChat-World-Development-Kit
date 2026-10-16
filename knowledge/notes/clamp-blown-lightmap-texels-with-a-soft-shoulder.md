---
title: Clamp a few blown lightmap texels with a soft shoulder instead of rebaking
topic: lighting-baking
tags: [lightmap, HDR, clamp, hot texels, emitter, post-process atlas]
summary: Isolated blown texels near an emitter can be fixed by a C1-continuous soft-shoulder clamp on the lightmap atlas, after proving those texels are actually sampled.
---
**When:** A bake next to a large emitter leaves isolated fully blown texels that render as hard white blobs reading as light sources. Rebaking a handful of texels is expensive and may not change them.

**How:** Clamp the atlas with a soft shoulder (a hard clip bands):
```
L' = CEIL - (CEIL - KNEE) * exp(-(L - KNEE) / (CEIL - KNEE))      for L > KNEE
```
It is continuous in value and first derivative at the knee and asymptotic to `CEIL`. Scale RGB by `L'/L` to preserve hue. In one scene (KNEE 0.25, CEIL 0.33) it touched 0.67 % of nonzero texels, took max luminance 257 to 0.33, left untouched texels round-tripping with zero error, and the offending blob went from 42x the window sky to 3x. Reading/writing needs a real RGBE `.hdr` codec.

**Pitfalls:**
- First prove the outlier is visible. A hot texel may sit in unsampled UV2 padding: a 257-luminance texel on one ceiling produced zero hot pixels from five player positions. Map the texel back to its renderer through every renderer's `lightmapScaleOffset`, then render from real player positions.
- A/B by re-rendering, not by re-reading the atlas, and re-sweep the whole scene, because a global clamp touches many renderers. Compare against pre-clamp per-renderer luminances.
- Keep a byte copy of the original `.hdr`. Any future rebake overwrites the clamp, so record it in the bake procedure.
