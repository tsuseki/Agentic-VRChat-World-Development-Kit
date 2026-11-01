---
title: Near-white atlas cells clip to flat white under a strong baked sun
topic: materials-textures-shaders
tags: [albedo, white, clipping, baked sun, atlas]
summary: Atlas whites near sRGB 241 clipped on 26.7 % of a sunlit view under a baked sun at x1.4; compress the top of the range in a world-owned atlas copy (above 185 into 185-210, hue kept) instead of a global tint.
---
**Symptom:** white plaster and linen cells of a shared structure atlas read as flat white patches in sunlit views
(26.7 % of pixels clipped in the reviewer's shot).

**Cause:** albedo ~sRGB 241 times a baked sun at intensity 1.4 exceeds display white.

**Fix / rule:** one world-owned atlas copy with a soft knee: values above sRGB 185 compressed into 185–210, hue kept.
A material `_Color` of 0.85 was rejected because it also dimmed wood, olive and charcoal cells. Author large white
cells at about sRGB 200 or below [INFERENCE from this fix]. Lower bright emitters in the same view too.

**Verify:** clipped-pixel % in the same sunlit shot before/after; dark cells unchanged.
