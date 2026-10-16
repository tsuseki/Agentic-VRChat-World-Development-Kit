---
title: On Mochie Glass, any non-zero _Roughness blurs the whole world behind the pane
topic: materials-textures-shaders
tags: [mochie, glass, grabpass, roughness, blur, reflections]
summary: Mochie/Glass gates a blurred grabpass on _Roughness > 0 and also uses it to pick a blurrier reflection mip, showing up as 'distant terrain is blurry' and 'glass has no reflections'.
---
**Symptom:** Reports like "the terrain is blurry far away" and "no reflection on the glass" in a scene where the outside is seen through Mochie glass. Hours lost on terrain LOD, basemap distance, fog and impostors.
**Cause:** `Mochie/Glass`:
```hlsl
if (_Roughness > 0 && _Blur > 0)
    grabCol = BlurredGrabpassSample(screenUV, roughness * blurStr);
```
At `_Roughness 0.25` / `_Blur 1` that is ~6 px at 1080p desktop (a quarter in single-pass stereo, so it is worse on desktop than in VR). The same value samples the reflection probe at mip ≈ `roughness * 1.7 * UNITY_SPECCUBE_LOD_STEPS` (~2.3) and lowers the grazing term.
**Fix / rule:** Keep `_Roughness = 0` on any Mochie glass you look through; get a frosted look with a roughness map only on panes that need it. When a "blurry background / no reflections" bug appears behind glass, read the glass material before investigating the world outside.
