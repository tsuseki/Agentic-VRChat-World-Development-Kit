---
title: Green/pink lightmap blotches: fix atlas starvation before blaming denoise or compression
topic: lighting-baking
tags: [bakery, lightmap atlas, scaleInLightmap, chroma noise, texel padding, BC6H, lightmap groups]
summary: Chroma blobs and bleed gradients on hero surfaces came from one hidden mesh eating 68% of the atlas; audit chart share, demote hogs, use fixed groups, pad, and bake at GI 32 / 4 bounces.
---
**Symptom:** Green/pink chroma patches and smooth dark bleed gradients on interior walls and doors after a Bakery bake; too many lightmaps in the scene.
**Cause:** Atlas starvation. An invisible exterior envelope mesh took 68.1% of a fixed 1024 atlas; a door got ~9 texels. Denoiser then smeared chroma noise across starved charts. Not compression (an uncompressed A/B showed identical patches) and not a video screen.
**Fix / rule (proven recipe):**
1. Audit chart share per renderer: `lightmapScaleOffset.x * lightmapScaleOffset.y` (share scales with `scaleInLightmap²`).
2. Demote hidden hogs (`m_ScaleInLightmap` 0.1), promote hero interior surfaces/props (2.0).
3. Fixed-resolution `BakeryLightmapGroup` (e.g. 2048) for the hero interior.
4. Terrain/background into one small shared fixed group (e.g. 512). Never leave terrains without a group selector — each grabs its own `maxAutoResolution` atlas (12 terrain tiles produced 11 of 17 lightmaps).
5. Edit → Project Settings → Bakery → texel padding (stored in `BakeryProjectSettings.asset`; default packer 3, xatlas 1) → 8. Which applies depends on the group's `atlasPacker`.
6. GI samples 32, bounces 4.
7. Lightmap importers `CompressedHQ` (BC6H). Bakery's default `CompressButAllowOverridingAsset` preserves per-texture Uncompressed overrides, so set importers explicitly post-bake.
8. Re-verify probes, re-render reflection probes, refresh light volumes.
Result: 17 lightmaps → 7, patches gone. Residual faint tint in the darkest creases: try "Denoise: fix bright edges", per-object sample multiplier, Backface GI.
**Pitfalls:** Dynamic-content screens (video players, mirrors) should not be ContributeGI — they bake their placeholder image as a coloured area light. LilToon/Mochie emissives are not found by `_EMISSION` keyword scans; check `_UseEmission` etc.
