---
title: Baked occlusion data hides moved static objects in editor captures
topic: agent-workflow-verification
tags: [occlusion culling, Umbra, capture, review renders, static objects]
summary: After a static renderer moves, the baked occlusion data still culls it by its old bounds, so a capture camera with occlusion culling on drops it whenever the old spot is out of view; review captures must render with useOcclusionCulling off, and the occlusion bake must be redone before upload.
---

**Symptom.** A wall picture moved to another wall showed in one capture and was missing from the next. Its renderer was enabled, active, not `forceRenderingOff`, and its bounds sat at the new spot. Its picture light, moved with it, was missing from both captures.

**Cause.** Static occlusion data (Umbra) stores static occludees with the bounds they had at the occlusion bake. A `Camera.Render()` with `useOcclusionCulling = true` (the default) culls a moved static renderer by its old visibility cell. If the old spot is behind the camera or hidden, the object vanishes at its new place. The same applies in play mode and in the uploaded world until occlusion is re-baked.

**Fix / rule.**
- Review and z-fight render cameras set `useOcclusionCulling = false`. The kit's `Util.Aim` does this for `__CapCam__`, so `WorldCapture` and `ZFightRender` show the scene as it is.
- Any move of a static renderer puts an occlusion re-bake on the pre-upload list (`StaticOcclusionCulling.GenerateInBackground`).
- Measurement cameras (perf sampling) keep occlusion on but must run after that re-bake.

**Verify.** Shoot the same view twice, with the capture camera's `useOcclusionCulling` on and then off. The moved object appears only in the second shot. After the occlusion re-bake, both shots match.
