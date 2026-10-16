---
title: A colour artifact in a screenshot may be an editor overlay, not the world
topic: agent-workflow-verification
tags: [screenshot, scene view, debug draw mode, selection outline, EditorPrefs, bug report]
summary: Before hunting a coloured artifact in assets, sample its exact RGB and compare it to editor overlay colours and Scene-view debug draw modes.
---
**Symptom:** A bug report of an "orange blinking bush"; some screenshots show the ground as a solid `#FF6600` dot field with moiré and rain as orange capsule outlines. Scans of every material, texture mip, light and fog uniform find no warm value anywhere.

**Cause:** Editor overlays, drawn after everything, on objects that share no material/shader/texture:
- The dot field was the **Scene-view Mipmaps debug draw mode**.
- `#FF6600` = `(1, 0.4, 0)` exactly matched `EditorPrefs.GetString("Scene/Selected Outline")` → the **selection outline**.
The tell: the colour was pure and clamped (1.000, 0.400, 0.000) with no fog blend or lighting falloff, in a night scene where nothing renders unfogged.

**Fix / rule:**
1. Measure the artifact's core pixels in sRGB and linear first.
2. If suspiciously round/saturated, check `EditorPrefs` (`Scene/Selected Outline`, `Scene/Selected Children Outline`, `Scene/Wireframe`) and Scene-view draw modes (Mipmaps, Overdraw, Lightmap) before touching an asset.
3. Establish which frames are Game view vs Scene view — Scene-view captures contain overlays that never ship. Don't assume a batch of screenshots shows one homogeneous defect; ask which are the real one.
