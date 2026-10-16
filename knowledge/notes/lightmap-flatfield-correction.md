---
title: Remove a smooth emitter-proximity ramp from a baked lightmap with a world-space flat-field
topic: lighting-baking
tags: [lightmap, post-process, flat-field, rgbe, hdr, gradient, atlas edit]
summary: Divide out a world-space, per-channel, low-frequency illumination field (gain ≤ 1) instead of rebaking or clamping; it preserves the high-frequency detail a clamp destroys.
---
**When:** An area emitter close to a surface baked a smooth 1/d² ramp across it, and rebaking is undesirable (it rebuilds atlases and wipes other hand-applied atlas edits) or a clamp would crush detail (e.g. a surface with no albedo texture whose mouldings live entirely in lightmap + normal map).
**How:** Estimate the low-frequency field, divide it out, clamp gain ≤ 1. Being smooth and multiplicative, each texel's ratio to its neighbourhood survives (measured high-frequency correlation 0.988, chroma 0.979). Four requirements, each a bug first:
1. **Estimate in world space, not UV space.** A UV blur bleeds across unrelated chart islands. Rasterize the mesh's uv2 into the atlas carrying interpolated world position, then blur over a 3-D grid.
2. **Per channel, not luminance** — the hot end is usually warmer too (second bounce).
3. **Weight fully shadowed (black) texels 0 when estimating** (normalized convolution); shadows aren't evidence about incident light.
4. **Reference mirror-image geometry at the 75th percentile** for a symmetric room. q75 not q50: with a one-sided gain clamp a median reference darkens half the reference region (−10% vs −4%).
**Pitfalls:**
- Kernel width is not free: sweep cell/radius/iterations and pick the setting that lands on the mirror reference value. Too wide drags toward darker surroundings.
- A "max relative error 1.0" on the RGBE round-trip is quantisation on near-zero texels; judge on untouched texels and bit-identity of unchanged regions.
- Assert nothing was brightened and the atlas max is unchanged.
- A soft-shoulder clamp's slope → 0 near the ceiling, flattening all high-frequency shading with the ramp.
