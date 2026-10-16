---
title: Use radial fog applied from your own shader uniforms — view-space fog makes edge "walls" and mirrors drop fog
topic: materials-textures-shaders
tags: [fog, radial distance, VRCMirrorReflection, mirror, surface shader, terrain, ExpSq]
summary: Built-in view-space fog thins toward screen edges so radial boundaries show as a peripheral wall, and VRChat mirrors render without Unity fog state; apply ExpSq fog unconditionally with radial distance from shader uniforms.
---
**Symptom 1:** A hard bright straight line in peripheral vision that vanishes when you look straight at it and tracks your head ("a wall in front of your vision") — at a 1000 m terrain edge with ρ = 0.00235 the boundary measured 1.0 8-bit levels dead ahead, 2.1 at 20°, **18.3** at the screen edge (45.7°), **26.4** in the corner.
**Symptom 2:** Distant geometry appears unfogged in every VRChat mirror (personal mirrors too).

**Cause:**
1. Built-in fog uses view-space depth `d·cosθ`, so anything ending at a constant *radial* distance (terrain boundary, ring of blocks) is under-fogged off-axis. A shortened far clip hides this (far-plane cuts are also view-space); restoring the far plane un-masks it.
2. The VRChat mirror pass renders **without Unity's fog state**: `FOG_*` keywords and `unity_FogColor` / `unity_FogParams` compile out or read zeros. A keyword-gated fix works on the main camera but not in mirrors.

**Fix / rule (per shader you control):** apply fog unconditionally from your own uniforms (e.g. `_WorldFogColor`, `_WorldFogDensity`, defaults matched to RenderSettings and **re-synced whenever scene fog changes**) with radial distance:
```hlsl
float f = density * distance(worldPos, _WorldSpaceCameraPos);
float fog = saturate(exp2(-f*f*1.442695));   // == RenderSettings ExpSq
```
- Multiply toward black in ForwardAdd passes; lerp to fog colour otherwise.
- Surface shaders: `finalcolor:` hook + `float3 worldPos` in Input; drop `multi_compile_fog` (useless in mirrors).
- Built-in terrain: a patched local copy of `TerrainSplatmapCommon.cginc` (a local cginc shadows Unity's copy).
- Stock Standard can't be hooked: clone it as a surface shader and swap materials (force `_Cutoff=0` on opaque mats whose albedo alpha is junk, zero emission where `_EMISSION` was off, preserve renderQueue).
- Every fogging shader (terrain, vegetation, impostors, bark/leaves) must use the same formula or ground and trees fog differently off-axis.
- The Water layer (4) never renders in mirrors at all.

**Verify:** sweep ≥12 bearings in play mode from open air and measure the strongest coherent horizontal step (median row-to-row luminance jump across full width): a fog wall reads 20–40 levels, a clean horizon ≤ ~1.5. Measuring from inside a room locks onto wall/ceiling junctions instead. `VRCMirrorReflection` doesn't render in ClientSim (white quad); to test in-editor, replicate with a manual camera: `reflectionMatrix * worldToCameraMatrix` + `Camera.CalculateObliqueMatrix` + `GL.invertCulling` + `RenderSettings.fog = false` + `cullingMask &= ~(1<<4)`.
