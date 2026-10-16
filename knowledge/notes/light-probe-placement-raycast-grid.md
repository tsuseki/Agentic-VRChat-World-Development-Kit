---
title: Place light probes with a raycast grid; auto-placers bury probes inside geometry
topic: probes-reflection-and-light
tags: [light probes, probe placement, magic light probes, raycast, dark spots]
summary: Auto-placement tools left probes inside roof shells and furniture (baked near-black), making dynamic objects go dark on furniture; a raycast-driven grid with no buried probes fixed it.
---
**Symptom:** Avatars/dynamic objects show position-dependent dark spots, especially when sitting on beds or furniture.
**Cause:** An auto-placement tool put probes inside the roof shell and inside furniture volumes (mattress probes L≈0.10 vs 0.20 in open air); buried probes drag interpolation dark.
**Fix / rule:** Delete the generated probe tree and build a grid by raycast. Per XZ column: cast down from above floor height for the floor, cast up from floor+0.25 for the ceiling; probes at floor+0.35 / floor+0.95 / ceiling−0.25; push candidates above furniture renderer bounds (+0.15); drop columns whose up/down rays sandwich them inside sealed wall/roof pockets. Result: 174 probes replaced 343 with zero dark ones.
**Pitfalls:**
- A probe-only render (`RenderLightProbesButton`) after editing `probePositions` worked without triggering Bakery's geometry-changed abort.
- Some post-process fixes (e.g. VRC Light Volumes' L1 probe fix) rescale SH values — judge uniformity across positions, not absolute levels.
**Verify:** Sample every probe's luminance; flag outliers well below the median (e.g. 0.08–0.11 vs a 0.21 median).
