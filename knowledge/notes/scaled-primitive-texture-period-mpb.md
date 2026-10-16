---
title: Scaled primitives sharing a material get different texture periods — fix with MaterialPropertyBlock
topic: materials-textures-shaders
tags: [MaterialPropertyBlock, tiling, _MainTex_ST, primitives, texture scale, batching]
summary: Unit cubes scaled to different lengths with one material show a different world texture period each; set _MainTex_ST per renderer from world size via MaterialPropertyBlock.
---
**Symptom:** Segments of a trim band using the same material look like different materials (fine pattern on short runs, coarse planks on long ones).
**Cause:** Object-space UVs on unit cubes scaled to 1.84–12.18 m: world period = length / tiling, varying 0.71–4.68 m per tile.
**Fix / rule:**
```csharp
const float PERIOD = 1.30f;   // metres per tile
var mpb = new MaterialPropertyBlock();
foreach (var r in bandRenderers) {
    float w = r.bounds.size.x;            // world width, not localScale
    mpb.Clear(); r.GetPropertyBlock(mpb);
    mpb.SetVector("_MainTex_ST", new Vector4(w / PERIOD, 1f, 0f, 0f));
    r.SetPropertyBlock(mpb);
}
```
- MPB instead of per-segment material copies (no extra assets or batch breaks). Standard routes normal/occlusion through `_MainTex_ST`, so maps stay registered.
**Verify:** `bounds.size.x / GetTextureScale("_MainTex").x` per renderer must be constant across the family. A grazing shot reveals it; head-on shots hide it. Confirm by render.
