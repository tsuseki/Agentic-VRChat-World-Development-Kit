---
title: Bakery SSS on a big fabric roof turns its underside into an area light
topic: lighting-baking
tags: [Bakery, SSS, computeSSS, sssColor, canopy, contact shadows, soffit]
summary: Per-group Bakery SSS on a large canopy can make the shaded underside brighter than sunlit ground and erase every contact shadow beneath it; scale it down with sssColor, not samples.
---
**Symptom:** After enabling Bakery per-group SSS (`computeSSS`) to rescue a near-black canopy soffit, the soffit measures brighter (luminance 0.70) than ground in full sun (0.60). Shade no longer reads as shade, and nothing under the roof casts a contact shadow: chairs, tables and walls meet the floor on a razor line with no AO.

**Cause:** A 33 x 27 m fabric roof with `sssDensity 5, sssColor white` becomes a giant soft overhead area emitter. The second symptom looks like missing shadows, which sends you hunting ContributeGI flags and texel density (both were fine: everything static, 7.3 cm/texel).

**Fix / rule:**
- Diagnose by measuring: **soffit luminance must be clearly below sunlit ground**. If a shaded surface is brighter than a sunlit one, SSS is the first suspect.
- Scale with **`sssColor`**: it is a linear multiplier on transmitted light, so white -> 0.5 grey roughly halves the contribution, predictably in one bake. Do not chase it with `sssSamples`; samples only affect noise (16 vs 256 gave an identical pattern and cost 24 min).
- Tint `sssColor` warm (e.g. 0.52, 0.47, 0.40): sun through cream canvas is not neutral.
- Residual ~0.6 m blotching on the soffit was per-triangle geometric SSS variation, not albedo tiling. Nulling `_MainTex` entirely leaves such a pattern unchanged; that one-bake test settles it.

**Pitfalls:** "No contact shadow" under **non-static** objects (e.g. parked vehicles) is a different cause: they are not in the bake at all. Add invisible `ShadowCastingMode.ShadowsOnly` proxy boxes marked ContributeGI.
