---
title: Realtime helper lights flatten a baked scene
topic: lighting-baking
tags: [Bakery, realtime light, preview, cullingMask, washed out, lightmap, AO]
summary: A temporary realtime directional light added to light an asset preview adds flat light to every lightmapped surface in a baked world; restrict it to its own layer or delete it before judging lighting.
---
**Symptom:** All upward-facing lightmapped surfaces (floors, some walls) look flat and washed out, as if the bake were broken. Ceilings look fine because they face away from the light, which disguises the cause.

**Cause:** A temporary realtime directional light was added to illuminate an out-of-bounds preview lineup. Baked lightmaps and realtime lights are additive; a shadowless directional light reaches everything regardless of its position and penetrates geometry, so the whole world receives flat additive light.

**Fix / rule:**
- Any helper/preview realtime light in a baked scene must have its `cullingMask` restricted to a dedicated layer (e.g. layer 22) with the preview objects moved to that layer, or be deleted before you judge lighting.
- Separately, check that Bakery AO is actually enabled when contact shadows under furniture are missing (`hackAOIntensity` can be 0 in a project's settings; 0.7 intensity / 0.4 radius worked).

**Verify (debug sequence that found it):**
1. Confirm the bake data is healthy: sample the `.hdr` atlas directly (Blit -> ReadPixels at UV2-interpolated positions). A statue shadow was present in the data but absent on screen.
2. Confirm renderer flags (`lightmapIndex`, `receiveGI = Lightmaps`).
3. Swap the floor to a plain white material. It rendered flat **bright**, not dark: that means an additive realtime light, not a missing lightmap.

Related: [sweep-leftover-capture-rigs-before-commit-or-bake](sweep-leftover-capture-rigs-before-commit-or-bake.md)
