---
title: Trees swapped in over baked light probes go dark on upward leaves; soften the L1 term until a re-bake
topic: probes-reflection-and-light
tags: [light probes, SphericalHarmonicsL2, LightingData, trees, probe-lit, crash]
summary: Probes baked with the old crowns shading them light new trees from below and darken upward leaves; until a re-bake, soften each probe's directional (L1) term so the darkest side is ≥ 30 % of the average, editing probes only through the scene's own LightingData.
---
**Symptom:** After replacing the trees in a baked scene, the new probe-lit crowns were dark on their upward-facing leaves.

**Cause:** The light probes were baked with the old crowns in place, so probes inside and under them recorded strong shading from above: their L1 (directional) term points down. The new crowns sample those probes.

**Fix / rule:** Re-bake. Until then, soften the directional term: per probe, scale the L1 coefficients until the darkest direction's irradiance is ≥ 30 % of the average (L0), and write the probes back through the scene's own LightingData (`LightmapSettings.lightProbes.bakedProbes`).

**Pitfall:** loading a second copy of the LightingData asset in the editor and editing that crashed Unity inside the light-probe update. Save the scene first, and edit probes only through the scene's loaded LightingData.

**Verify:** evaluate each edited probe over 6 axes (`SphericalHarmonicsL2.Evaluate`) and check min/mean ≥ 0.3; render the crowns from below and from eye height.
