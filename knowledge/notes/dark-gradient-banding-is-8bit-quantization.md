---
title: Banding on big dark surfaces is 8-bit backbuffer quantization, fixed with a screen-space dither
topic: materials-textures-shaders
tags: [banding, dither, linear-color-space, 8-bit, dark-scenes, shader, overlay]
summary: Contour bands across a large dark gradient are usually 8-bit backbuffer quantization rather than a bake defect; no texture or rebake fixes it, a multiplicative screen-space dither does.
---
**Symptom:** Contour bands step across a big dark ceiling right after a lighting pass, so it looks like a bake regression.

**Diagnose in this order** (the first two exonerate the bake, the third convicts):
1. Lightmap mean on the renderer before/after (e.g. 0.0222 -> 0.0224: nothing regressed).
2. Float lightmap profile along the gradient: 158 distinct values over 240 texels, longest identical run 3 -> the bake is smooth.
3. **Render the same camera to `ARGB32`/sRGB and to `ARGBFloat`/Linear and count distinct values.** 435 float values vs **44** 8-bit levels over 700 px = ~16 px per code value, exactly the band spacing. Definitive.

**Pitfalls:**
- A texture cannot fix it. A finely tiled fabric renders through a high mip: 8.2% contrast at full res collapsed to 1.09% averaged over 8x8 texels - under a third of one 8-bit level. Retiling changed nothing. Detail below one code value contributes nothing at any tiling.
- A dither applied to an already-quantized PNG can never work; it must happen before quantization.

**Fix:** a multiplicative screen-space dither on a head-locked overlay quad (no post stack needed):
`out = scene * (1 - _Dim) * (1 - _Dither * ign(pixel))`, `Blend DstColor Zero`, strength ~0.06, interleaved-gradient noise, **static** in screen space (animated noise shimmers in VR).
- **Multiplicative, not additive.** In Linear colour space a fixed additive offset is a huge encoded step near black and invisible in highlights. A relative scale moves the sRGB value by about the same number of levels at every brightness (`dE/E ~ (1/2.4) dL/L`, so 0.06 ~ 1.2 levels).
- **One-sided (always scales down).** An LDR pass clamps at 1.0, so a symmetric swing loses its bright half. Cost is ~0.6 level uniform darkening; pure black stays black.
- Put any screen dimmer on the same quad: dimming a dark scene crushes it into fewer code values, so a dim slider makes banding worse.

**Verify before writing the shader:** render to a float RT, apply `(1 - s*hash)` in C#, sRGB-encode, quantize to 8-bit, save both images. Zero project mutation, and it settles the strength.
