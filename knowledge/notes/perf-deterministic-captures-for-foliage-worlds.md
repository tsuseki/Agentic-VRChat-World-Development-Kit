---
title: Deterministic before/after captures in foliage worlds: freeze wind, fades, water and particles
topic: agent-workflow-verification
tags: [pixel diff, capture, wind, LOD cross-fade, MaterialPropertyBlock]
summary: Foliage captures differ run to run until wind, LOD cross-fade, animated water and particles are frozen; two consecutive 'before' sets must match at 0 px before any diff counts.
---
**Symptom:** same-camera diffs of a forest world showed scattered changes between two captures of an unchanged scene.

**Cause:** shader wind (time-driven), LOD cross-fade dither, animated water and particles.

**Fix / rule:**
- Freeze wind with a MaterialPropertyBlock (`_WindSpeed` = `_FlutterSpeed` = 0) on renderers whose
  `shader.name.Contains(...)` the wind shader's name (`Contains`, so cell and world copies of the shader freeze too).
- Every `LODGroup.fadeMode = None` for the capture, restored afterwards (in `finally` for a synchronous renderer, after
  `COMPLETE` for an async one).
- Hide animated water and every `ParticleSystemRenderer` (`forceRenderingOff`).
- One persistent capture camera; 1280×720 at 77.4° vertical FOV (≈ 110° horizontal); per pose an eye-height view, a
  look-down view (pitch 25°) and a back view.
- Two consecutive "before" sets must be bit-identical (0 px). Report % of pixels with summed RGB difference > 18 plus
  "any change".

**Pitfalls:** `SetPropertyBlock(null)` also clears blocks other systems own on those renderers; the fadeMode toggle
dirties the scene, so reopen or re-save it in edit mode afterwards. [INFERENCE, from a shader read] Wind whose static
wave terms use world position keeps a position-dependent rest pose at speed 0, so the same object at another world
offset (a scene copy recentred at the origin) need not render identically; compare like-for-like positions.

**Verify:** the 0-px repeat pair, quoted with every diff.
