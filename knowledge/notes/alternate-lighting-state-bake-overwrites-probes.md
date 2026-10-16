---
title: Baking an alternate lighting state overwrites the shared light-probe asset
topic: probes-reflection-and-light
tags: [light probes, bakery, day night, probes.asset, spherical harmonics, avatars]
summary: A scene with day/night states has one probes asset; baking the night state leaves the day state lighting avatars with night probes — fingerprint: every probe has the same chromaticity.
---
**Symptom:** After baking an alternate (e.g. night) lighting state, the default state's lightmaps look right but avatars and other dynamic objects are lit wrong (often reported as "light volumes stuck in night mode").
**Cause:** Bakery/Unity rewrite the single `BakeryLightmaps/<scene>_probes.asset` on any full render. Lightmaps are per-state; probes are not.
**Fix / rule:**
- Before baking an alternate state, know whether it writes the probe asset and snapshot it. Check git — the asset may be tracked even when its folder looks ignored.
- After restoring the asset, **reopen the scene**: `AssetDatabase.Refresh(ForceUpdate)` does not rebind; `LightmapSettings.lightProbes` is a cached "(Clone)" and re-measures byte-identical.
**Verify:**
- Measure probe chromaticity spread in the default state. A single-coloured source gives every probe one hue (measured: all 176 probes r/b = 0.237); correct day probes spread widely (r/b 1.77–3.06). A whole room agreeing to three decimals is never physical.
- Compare brightness with `SphericalHarmonicsL2.Evaluate(dirs, results)` averaged over 6 axes, not the raw DC term `sh[c,0]*0.282095` (that understated day ~3.5× and invented a false alarm).
