---
title: Cutout leaf cards shimmer in VR at MSAA 4x; fix with alpha to coverage plus a far-only mip bias and cutoff drop
topic: materials-textures-shaders
tags: [trees, foliage, shimmer, aliasing, alpha to coverage, mip bias, MSAA, VR, measurement]
summary: Alpha-cutout leaves ~1 px wide flicker as the head turns; MSAA alone does nothing and A2C alone ~8 %. Ramping a +0.35 mip bias and a −0.05 A2C cutoff drop in only once the leaf texture is minified past mip 1 cut flicker above a supersampled reference ~45–70 % at 6–40 m, kept crown coverage within 1 point and left near leaves untouched; measured with a sub-pixel camera-yaw metric.
---
**Symptom:** Leaf-card trees in VR "blink and shimmer" when the head moves, even at VRChat's default MSAA 4x. The flicker covers the whole crown interior, not just the silhouette: at ~9 m the leaves are ~1 px wide.

**Cause:** An alpha cutout is an on/off decision per pixel, and MSAA doesn't sample the alpha test, so the result jumps between frames. Alpha to coverage (A2C) on its own only softens edges by 4 levels; the texture under it is still sub-pixel.

**Fix / rule:** In the leaf path compute the texture LOD from `ddx/ddy(uv)` × texel size, `far = saturate(lod − 1)`, then:
- sample with `tex2Dgrad(uv, dx·g, dy·g)` where `g = exp2(bias · far)` and bias = 0.35;
- with A2C on, use cutoff `_Cutoff − 0.05 · far`;
- keep the shadow and meta passes at the plain cutoff.

Settings that failed:
- a global bias blurs near leaves, and bias 2 turns them blobby;
- bias 0.75 clumps far sprays into dark lumps;
- A2C without the cutoff drop thins far crowns ~10 %;
- a 0.1 drop overfills them by 3–4 points and makes outer sprays solid;
- a soft A2C ramp (min edge width) raised flicker.

Cost: A2C's 4-level dither raises the whole-pixel crawl (about 4 → 10–20), still under half of Silent's Crispy Foliage.

**Verify:** Measure on a pure camera yaw of 0.25 px per frame, 20 frames, alpha cutout vs a 4× supersampled + MSAA 8 reference of the same view.
- Flicker = mean |next(x) − (0.75·this(x) + 0.25·this(x−1))| over the crown mask, frame to frame. A whole-pixel-shift comparison is blind to cutout aliasing; use it only to see A2C dither crawl.
- Coverage = the target alone over a black and a white clear, alpha = 1 − (white − black). A luminance-difference proxy disagreed with this by ~3 points.
- Check 6, 9, 20 and 40 m, plus a 1.5 m close-up to confirm near leaves are unchanged.
- Implementation: `ShimmerLab.cs`, kept in the tree-pack project's `_Dev/Editor`.
