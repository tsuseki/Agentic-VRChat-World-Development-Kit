---
title: Match the HDRI skybox sun to the baked sun in azimuth as well as elevation
topic: lighting-baking
tags: [skybox, hdri, sun, directional-light, azimuth, _Rotation]
summary: A skybox sun matched to the baked directional light in elevation only can sit 180 degrees out in azimuth, putting the visible sun on the same side as the shadows; measure both and fix with the skybox _Rotation.
---
**Symptom:** The sun disc in the sky and the shadows on the ground are on the same side of the frame; the patch of sky the light comes from is empty. Each half looks fine alone and nothing warns. Example: HDRI sun az 34 / el 42 vs baked sun az -145 / el 43 - elevation within 1 degree, azimuth 179 degrees out.

**Fix / rule - measure, don't eyeball:**
- Render the skybox alone (camera `cullingMask = 0`, `clearFlags = Skybox`) and sweep for peak luminance: coarse az -180..180 step 8, el 0..70 step 8, FOV 10; refine +/-8 degrees at step 2, FOV 5. The HDRI sun is enormous (~64,000 vs ~1 for sky), so the peak is unambiguous.
- Light direction: `toSun = -light.transform.forward`, `az = Atan2(toSun.x, toSun.z) * Rad2Deg`, `el = Asin(toSun.y) * Rad2Deg`. Shadows extend toward `Atan2(fwd.x, fwd.z)`; if that equals the sky sun's azimuth, the skybox is reversed.
- Fix with `_Rotation` on the `Skybox/Cubemap` material - cosmetic, no lightmap rebake. Solve the sign empirically (set, re-measure, adjust). Re-render reflection probes afterwards, since they capture the skybox.
- Check azimuth every time a skybox is swapped or the sun re-aimed.

**It's genuinely cosmetic:** baked under-object / clear-ground luminance ratios were 0.41-0.45 before and 0.42-0.46 after a full rebake. What improves is readability - the frame isn't washed out by a sun glowing where shadows point. Don't sell it as a shadow-contrast fix.

**Verify:** two renders - toward the light's azimuth (sun in frame, geometry backlit) and away (shadows point at camera).
