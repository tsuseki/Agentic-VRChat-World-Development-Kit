---
title: With _EMISSION disabled, an _EmissionColor MaterialPropertyBlock silently does nothing
topic: materials-textures-shaders
tags: [emission, MaterialPropertyBlock, shader keyword, _EMISSION, Standard shader]
summary: The forward pass branches on the _EMISSION keyword, so a property-block emission colour on a material with the keyword off applies, reads back correctly, and never renders.
---
**Symptom:** You drive `_EmissionColor` through a `MaterialPropertyBlock` (night mode, highlight state). `HasPropertyBlock()` is true, the value reads back exactly, no console entry — and nothing glows.

**Cause:** The material's `_EMISSION` keyword is disabled; the forward pass never reads the property. Imported materials often ship this way, frequently also with `globalIlluminationFlags = EmissiveIsBlack`.

**Fix / rule:**
- `mat.EnableKeyword("_EMISSION")` on the material asset.
- **Set `globalIlluminationFlags = None`, not `EmissiveIsBlack`, on any material that must glow.** Unity's Standard shader GUI (`SetMaterialKeywords`, run by `ValidateMaterial` when the `.mat` is imported or validated, and by the inspector) keeps a flag of exactly `EmissiveIsBlack` and then sets `_EMISSION` = flag absent. A keyword you enabled therefore turns itself off at the next validation. Measured: an LED material written with `_EMISSION` on + `EmissiveIsBlack` read back keyword off and rendered black. `None` keeps runtime-only emission out of bakes just the same. Bakery and Progressive only take emission from `BakedEmissive`.
- Snapshot prior keyword state before changing it.

**Verify:** before relying on an emission property block, dump `IsKeywordEnabled("_EMISSION")`, `HasProperty("_EmissionColor")` and `_EmissionMap` for every material in the list. An emission map attenuates whatever you set (one set of fixtures measured ~0.107×), so calibrate by measuring the render, not by the typed value.
