---
title: With shared LOD lightmap UVs, far LODs give no texels back; atlas size is the only lever
topic: lighting-baking
tags: [BakerySharedLODUV, LOD, texel density, atlas size]
summary: When LOD1/LOD2 reuse LOD0's lightmap chart (Bakery shared LOD UV), there are no far-LOD texels to move; the density trade is atlas size alone (median 4.59 → 2.10 texels/m going to one 4096).
---
**Symptom:** a plan to fit a trees group into a smaller atlas by moving texels off far LODs found nothing to move.

**Cause:** with shared LOD UVs (`BakerySharedLODUV`), LOD1 and LOD2 sample LOD0's chart; only LOD0 charts take atlas
space.

**Fix / rule:** decide the atlas size from the LOD0 density you accept. Median texels/m over 3,676 LOD0 charts: 4.59 in
the source scene, 2.10 with one 4096², 3.02 with two 4096². At one 4096 the canopy self-shadowing visibly weakened.

**Verify:** median texels/m from baked scale-offsets, plus lightmap-only renders of the canopy at each candidate size.
