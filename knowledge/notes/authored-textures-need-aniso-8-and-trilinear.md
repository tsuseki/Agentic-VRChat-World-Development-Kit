---
title: Authored textures import at aniso 1 / Bilinear and look smeared at grazing angles
topic: materials-textures-shaders
tags: [texture-import, anisotropic, trilinear, mipmaps, grazing-angle, uv-stretch]
summary: Textures written by scripts or dropped in by hand import at anisoLevel 1 and Bilinear, which smears directional grain on floors and walls and is routinely misdiagnosed as a UV problem.
---
**Symptom:** A reviewer flags "strong anisotropic UV stretching" on a wall or floor lining. A UV pass re-rates every panel to world scale and measures a perfect 1.00 isotropic stretch ratio - and the smear is still there.

**Cause:** The texture was imported at `anisoLevel = 1`, `filterMode = Bilinear`. Stock asset-pack materials that look right sit at `anisoLevel = 8`, `Trilinear`. Narrow spaces viewed almost entirely at grazing angles (saunas, corridors, floors) are exactly where low aniso destroys directional grain. In one project a sweep found 83 of 99 authored textures still on the import default - only imported asset packs come pre-configured.

**Fix / rule:** Run once per project and again after any batch of authored textures:

```csharp
var ti = AssetImporter.GetAtPath(p) as TextureImporter;
bool dirty = false;
if (ti.anisoLevel < 8) { ti.anisoLevel = 8; dirty = true; }
if (ti.filterMode != FilterMode.Trilinear) { ti.filterMode = FilterMode.Trilinear; dirty = true; }
if (!ti.mipmapEnabled) { ti.mipmapEnabled = true; dirty = true; }
if (dirty) ti.SaveAndReimport();
```

**Diagnostic order for "the texture looks smeared":** compare import settings against a stock surface that looks right **before** touching UVs, and never start by touching geometry. It is one property read.

Related: [uv-density-may-live-in-the-material](uv-density-may-live-in-the-material.md), [npot-textures-lose-aspect-and-compression](npot-textures-lose-aspect-and-compression.md)
