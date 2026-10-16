---
title: Tell dark geometry from a baked shadow by re-rendering the same pixel with the renderer disabled
topic: lighting-baking
tags: [dark line, baked shadow, albedo, renderer toggle, lightmap sampling, diagnosis]
summary: To decide whether a dark band is a baked shadow or simply dark geometry, render twice from a fixed camera with the suspect renderer on and off and compare the same pixel — not against "the surface either side".
---
**Symptom:** A dark stripe on a ceiling ridge. Comparing "trough vs flanks" gives contradictory answers (1.22× brighter or 7:1 darker) depending on where the side samples land in a lighting gradient.

**Fix / rule — toggle test:** render twice from one fixed camera, suspect renderer `enabled = true` then `false`, compare **the same pixel index**:
- Pixel gets much **darker** with the renderer hidden → those pixels *are* that geometry; you're seeing its albedo. A dark trim reading dark is not a defect. (Measured: 0.0078 with the cap, 0.0008 without — the line was the cap's dark wood.)
- Pixel **unchanged** → the darkness is baked into whatever is behind; the occluder is still casting.

**Second use — ghost shapes after deleting a shadow caster:** deleted lightmapped objects leave their baked shadows in the atlas until you rebake. Soft dark chips that look like new geometry poking through are often old shadows; the toggle test shows the suspected geometry owns 0 px there. Prove ownership before "fixing" innocent geometry.

**Faster alternative:** sample irradiance through each renderer's `uv2 * lightmapScaleOffset` from a `Graphics.Blit` copy of `LightmapSettings.lightmaps[i].lightmapColor`. Separates "unlit" from "dark albedo" in one call (e.g. cap mean irradiance 0.102 vs surface behind 0.021 → the cap is well lit, just dark-coloured).
