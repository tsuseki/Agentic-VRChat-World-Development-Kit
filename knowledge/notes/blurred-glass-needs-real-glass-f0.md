---
title: Blurred glass reflections need real-glass F0 (0.04), not Standard's 0.0083
topic: probes-reflection-and-light
tags: [glass, fresnel, F0, reflection probe, smoothness, blur, WindowGlass]
summary: Blurring a glass reflection (smoothness 0.90 → 0.70) spreads the same energy thin, so a 0.0083 head-on reflectance vanishes and the glass seems to reflect only at an angle; use F0 0.04 with Standard's Pow4 curve and 0.71 cap.
---
**Symptom:** After glass smoothness went from 0.90 to 0.70 to blur the reflection, the user said
"reflection is barely visible now", then "so reflection is kinda only visible at an angle". A first
fix with a `pow5` curve capped at 0.45 was still "too faint".

**Cause:** The look approved earlier was Standard Specular, `_SpecColor` 0.09 sRGB = 0.0083 linear,
which is about 1/5 of real glass. A sharp mirror image is readable even at 0.8%. A blurred one spreads
the same energy over the pane and drops below what anyone notices, so only the Fresnel rise near
grazing stays visible. The capped `pow5` curve also under-reflected at oblique angles compared with
Standard's `lerp(F0, smoothness + F0, Pow4(1 − N·V))`.

**Fix / rule:** Use Standard's Pow4 curve, F0 **0.04** (real glass, n = 1.5), grazing **0.71**, smoothness
0.70, and leave the exterior probes at their approved intensity (3.0). The glass stays see-through
because alpha is `1 − (1 − F0)(1 − tint alpha)`, as in Standard's premultiplied mode. At oblique
angles the curve matches real glass within a few points out to ~80°. Full recipe:
`.omp/skills/materials-shaders/references/window-glass.md`.

**Verify:** Use glass-on minus glass-off luma at the same camera (mean / p95 / % pixels over diff > 2).

| Pose | F0 0.0083 | F0 0.04 |
|---|---|---|
| Outside head-on, mean | 10.7 | 15.6 |
| Inside looking out, mean | 10.5 | 25.9 |
| Near-grazing, mean | 21.8 | 20.8 |

Head-on rose; the grazing pose barely changed. The user accepted the F0 0.04 result.

**Pitfalls:** Changing `ReflectionProbe.intensity` from a script (1.15 and back to 3.0) left the same
material settings measuring 4.7 instead of 10.7 until the scene was saved and reopened. Reload the
scene before trusting a drop in numbers after probe edits. Don't use probe intensity ×5.5 or F0 0.45
to make up for the blur: that is the milky, opaque look.
