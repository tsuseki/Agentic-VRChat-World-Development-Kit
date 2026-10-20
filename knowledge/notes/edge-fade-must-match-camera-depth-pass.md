---
title: A view-dependent leaf edge fade must also clip the camera-depth pass, or faded cards leave white ghost slivers over shadowed ground
topic: materials-textures-shaders
tags: [trees, foliage, edge fade, shadows, screen-space shadows, ShadowCaster, camera depth, built-in RP]
summary: In the Built-in RP the directional light's screen-space shadow collector reads the camera depth texture, which Unity draws with the ShadowCaster pass. If the leaf card's edge fade runs only in the colour pass, a faded edge-on card is gone from colour but still in depth, so the ground behind it samples the card's unshadowed depth and shows a bright leaf-shaped ghost. Apply the fade in the ShadowCaster pass only when unity_LightShadowBias is zero (camera depth); light shadow maps keep the full silhouette.
---
**Symptom:** Cards seen near edge-on, in front of shadowed ground, render as bright white leaf-shaped slivers. Drawn alone (no scene, no shadows) the same cards show nothing.

**Cause:** The surface shader fades cards by view angle (`|cos|` between the screen-derivative face normal and the view) in the forward colour pass, but `addshadow` generates a ShadowCaster pass that clips only at `_Cutoff`. Unity also renders the **camera depth texture** with that pass, and the screen-space directional shadow collector reconstructs world positions from it. The faded card still writes depth, so the ground pixels behind it get the card's (lit) shadow lookup.

**Fix / rule:** Compute the fade once; in `UNITY_PASS_SHADOWCASTER` multiply alpha by it only when `unity_LightShadowBias.x == 0 && unity_LightShadowBias.z == 0` (Unity zeroes it for the camera depth pass), then clip. Light shadow maps and the meta (bake) pass keep the whole leaf silhouette. A light with depth and normal bias both at 0 would also get the fade; keep the default biases.

**Verify:** Same camera, same scene, before/after; the before must show the ghost (positive control). Wind moves leaves between renders, so judge the crop by eye, not a whole-frame pixel diff. Check the ground shadow is still leaf-shaped (shadow map unchanged).
