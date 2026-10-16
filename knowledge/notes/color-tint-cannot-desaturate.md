---
title: A material colour multiply darkens but cannot desaturate
topic: materials-textures-shaders
tags: [_Color, tint, saturation, albedo, texture, desaturate, shared material]
summary: _Color scales R, G and B proportionally, so a grey tint only darkens; fix a garish or warm texture by swapping or desaturating the texture itself.
---
**Symptom:** A prop reads too orange/garish against a neutral scheme. Multiplying `_Color` down makes it darker (value 0.64 to 0.29) but the complaint stays.

**Cause:** `_Color` is a **multiply**. Saturation is a ratio between channels, and a neutral (grey) multiply scales all channels equally, so the loud pixels stay exactly as loud relative to their neighbours. A *coloured* tint (e.g. bluish over a warm texture) does change channel ratios: crude but real chroma correction. Replacing such a coloured tint with a neutral grey one, without doing the texture work, silently reverts the fix.

**Diagnose with the right statistic:** mean colour is the wrong oracle for "garish". A dark texture with one neon area has a low mean and a high peak, and the eye lands on the peak. Score on `p95` of per-pixel saturation and `hot` = fraction of pixels above a saturation+value threshold.

**Fix / rule, in order of preference:**
1. Swap the texture (the only real fix for photo/art content).
2. Desaturate the texture itself into a new asset: blit through a `RenderTexture` (source assets are rarely `isReadable`), `ReadPixels`, per pixel `lerp(luminance, rgb, 0.16)` with an optional slight bias, `EncodeToPNG`, import, assign. In one case saturation went 0.616 to 0.166.
3. Tint only to darken something already neutral in hue.

Always clone the material before tinting: pack materials are often shared by dozens of renderers across the world. When a review says "do A **and** B" (tint and desaturate), doing A alone can be a regression.

**Verify:** Judge albedo under a near-white inspection light. Under warm sconces a correctly neutral object still reads tan and invites a second wrong fix.
