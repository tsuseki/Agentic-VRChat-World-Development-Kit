---
title: Light Volume PBR reads AO from the metallic map's G channel and squares metallic
topic: materials-textures-shaders
tags: [Light Volume PBR, metallic map, ambient occlusion, channel packing, _LV.mat]
summary: Light Volume PBR's 'Metal AO Smoothness' map is R metallic (times _Metallic, then squared), G AO, A smoothness; a Standard-style MetallicSmoothness map with metallic copied into G turns every non-metal black.
---
**Symptom:** after switching a structure atlas's materials to `Light Volume Samples/Light Volume PBR` (`_LV.mat`
copies), every non-metal cell rendered black, before and after the bake.

**Cause:** in the shader, `_MetallicGlossMap` ("Metal AO Smoothness") is read as metallic = `(R × _Metallic)²`,
AO = `lerp(1, G, _OcclusionStrength)` multiplying indirect light plus speculars, smoothness = `A × _Glossiness`.
Defaults: `_Metallic 0`, `_Glossiness 1`, `_OcclusionStrength 1`, map white. The source map had G = metallic, so AO
was 0 wherever metallic was 0.

**Fix / rule:** pack the map for this shader: R = √(target metallic), G = 255 (or real AO), B = 0, A = smoothness, and
set `_Metallic 1`. `_OcclusionStrength 0` is only a stopgap: it also drops AO on the metal cells.

**Verify:** a non-metal cell's brightness matches its Standard original in a same-camera pair; metal cells keep their
reflection.
