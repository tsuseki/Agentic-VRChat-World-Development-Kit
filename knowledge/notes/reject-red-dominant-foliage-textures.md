---
title: A plant that looks dead under every light has a red-dominant albedo — replace the asset
topic: materials-textures-shaders
tags: [foliage, albedo, texture audit, plants, colour]
summary: Measure each foliage texture's alpha-weighted mean RGB; healthy plants are G > R, and any R > G asset reads as dried/dead at every light level.
---
**Symptom:** A potted plant looks grey-brown/dried next to a green plant under the same light. Relighting and tinting do nothing.
**Cause:** The pack ships a dried-plant texture (mean RGB 0.44/0.35/0.28). `_Color` was already white; it was never a lighting problem. Dark night scenes hide it until something green stands nearby.
**Fix / rule:**
- Blit each foliage `_MainTex` to a small RenderTexture, read back, take the **alpha-weighted** mean (cutout backgrounds pollute an unweighted mean). Healthy foliage measured G > R (e.g. 0.27/0.38/0.19); reject any asset with R > G.
- Sweep the class: find every renderer using the offending material (earlier placements included), record world bounds (centre XZ + min Y), instantiate the replacement, re-centre XZ, seat min Y, keep parent and sibling index.
