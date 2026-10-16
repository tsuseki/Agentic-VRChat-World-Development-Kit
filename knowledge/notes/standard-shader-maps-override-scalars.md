---
title: On Standard shaders a bound map silently overrides the scalar you edit
topic: materials-textures-shaders
tags: [Standard shader, smoothness, _Glossiness, _MetallicGlossMap, _EmissionMap, keywords, specular highlights, glossy reflections]
summary: Smoothness, metallic and emission edits on Standard materials silently no-op when a gloss map, albedo-alpha smoothness, stale keyword or emission mask is in play; inspect maps and keywords, and verify on a render.
---
**Symptom:** A "make it less shiny" or "make it glow" fix changes the inspector value but the frame is unchanged (sometimes byte-identical), which sends you chasing reflection probes or lighting.

**Cause / override paths:**
1. **`_MetallicGlossMap` bound:** smoothness comes from the map's alpha; `_Glossiness` is ignored (a 0.05 material rendered mirror-glossy off a default-white map). Metalness then comes from the map's red channel and `_Metallic` is a no-op too: binding a steel metal/smoothness pack to a *painted* material drove metalness to 1, and with no baked reflection probe metal = 1 has no diffuse term, so painted props rendered near-black.
2. **`_SMOOTHNESS_TEXTURE_ALBEDO_CHANNEL_A`:** smoothness comes per texel from the albedo alpha (`_Glossiness = 1.00` rendered ~0.22 because authored alpha was 0.17-0.27). Scaling the authored alpha keeps the per-texel variation; replacing it with a scalar throws it away.
3. **Stale keywords after `CopyPropertiesFromMaterial`:** a clone keeps `_METALLICGLOSSMAP` / `_SPECGLOSSMAP` even after you null the map, so it samples a default white map. Disable keywords explicitly after cloning.
4. **Smoothness 0 with no maps is still shiny:** Standard / Autodesk Interactive keep sampling the reflection probe (mirror streaks via the normal map). Full kill needs both specular paths, each with float **and** keyword: `_SpecularHighlights 0` + `_SPECULARHIGHLIGHTS_OFF`, and `_GlossyReflections 0` + `_GLOSSYREFLECTIONS_OFF`.
5. **`_EmissionColor` is multiplied by `_EmissionMap`:** a pack-authored emission mask that is black over the object's UVs makes any emission colour produce 0 changed pixels; `SetTexture("_EmissionMap", null)` restores the white default. A material that binds its own albedo as emission map lifts only the content, never a black background.

**Fix / rule:** Before tuning, check `HasProperty`/`GetTexture` for `_MetallicGlossMap` and `_EmissionMap`, the shader keyword list, and whether the albedo has authored alpha. Only bind a metal/smoothness map when the material really is metal. An albedo scan reused as a tint multiplier must be desaturated and mean-normalised first, or its own colour wins (rust-red scan x blue tint = maroon).

**Verify:** On a render, never on the inspector value. A zero-pixel diff after a change means you edited the wrong input.

Related: [repurposing-pack-materials-clear-every-map](repurposing-pack-materials-clear-every-map.md), [metallic-depends-on-what-the-reflection-probe-sees](metallic-depends-on-what-the-reflection-probe-sees.md)
