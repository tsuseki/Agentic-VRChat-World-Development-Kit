---
title: With Bakery, Baked-mode reflection probes lose their cubemap on reload — use Custom mode
topic: probes-reflection-and-light
tags: [reflection probe, bakery, lighting data asset, custom baked texture, blue sheen, skybox fallback]
summary: A Baked reflection probe's cubemap reference lives in the LightingDataAsset, which Bakery does not populate, so it is lost on scene reload; set mode=Custom with customBakedTexture.
---
**Symptom:** Glossy walls/ceilings show a blue (sky-coloured) sheen; or the world ships with effectively no reflection probes. Any screenshot taken in the same session as the probe bake looks correct, so reviews never catch it.
**Cause:** A `Baked` probe's cubemap is referenced from the LightingDataAsset, not the scene. Bakery's LDA holds only lightmaps/probes, so after reload the probe is `mode=Baked, bakedTexture=NULL` and specular falls back to the skybox.
A second, separate cause of blue sheen: sky light baked into the lightmap from hidden exterior faces whose charts bleed into interior charts, or skylight entering from below through glazing.
**Fix / rule:**
- Set `mode = Custom` and `customBakedTexture` = the baked `.exr`. It serialises as `m_CustomBakedTexture: {guid: …}`, survives reloads and builds, and re-baking to the same path updates it.
- Bake with `Lightmapping.BakeReflectionProbe(probe, path)` or Bakery's `RenderReflectionProbesButton(false)`, always after the lightmap bake. Box-projected probes' Y range must cover the ceiling.
- For baked-in sky bleed, a bake-only dark blocker plate under the floor/hull (active during bake, disabled after, before probe render) helps.
**Verify:**
- Grep the scene YAML for `m_CustomBakedTexture`, never by reading `bakedTexture` live (true now, false after reload).
- A/B: set `RenderSettings.reflectionIntensity = 0` and screenshot — if blue persists it is baked into the lightmap. Also check `reflectionIntensity` is 1, or every gloss change will look invisible.
