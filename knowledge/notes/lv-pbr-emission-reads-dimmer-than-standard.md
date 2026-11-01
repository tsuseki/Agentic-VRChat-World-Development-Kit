---
title: Emission reads about half as bright on Light Volume PBR as on Standard
topic: materials-textures-shaders
tags: [Light Volume PBR, emission, _LV.mat, glow]
summary: Moving an emissive prop from Standard to Light Volume PBR halved its visible glow (2,463 → 1,045 glowing px); turn speculars off, smoothness 0 and raise _EmissionColor (2.2 → 5.5) to match by pixel count.
---
**Symptom:** a coal bed's glow nearly vanished after its material moved to `Light Volume Samples/Light Volume PBR`
(glowing pixels in the reviewer's crop 2,463 → 1,045).

**Fix / rule:** clear `_SPECULARS_ON` (`_Speculars 0`), set `_Glossiness 0`, and calibrate `_EmissionColor` by the
same-camera glowing-pixel count against the Standard original: 2.2 → 5.5 matched (Standard 1,190 px vs LV 1,187;
4.4 gave 823 and 5.7 gave 1,257).

**Verify:** same-camera crop, glowing-pixel count within a few % of the Standard original.
