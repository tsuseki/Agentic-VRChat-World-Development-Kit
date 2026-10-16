---
title: Convert ambientCG PBR sets to Unity Standard offline, and tame _GlossMapScale
topic: materials-textures-shaders
tags: [ambientCG, Standard shader, channel packing, smoothness, roughness, normal map, tiling, ProBuilder]
summary: Pack inverted roughness into the metallic map alpha, use the GL normal, and drop _GlossMapScale well below 1.0 or polished stone turns into a black mirror.
---
**When:** Turning an ambientCG zip (`_Color`, `_NormalGL`, `_NormalDX`, `_Roughness`, sometimes `_Metalness` / `_AmbientOcclusion`) into a Built-in Standard material. Convert offline (PIL, seconds) rather than hand-wiring in the editor.

**How:**
- Standard's `_MetallicGlossMap` is **R = metallic, A = smoothness**. ambientCG ships roughness, so invert:
  ```python
  smooth = Image.eval(rough_L, lambda v: 255 - v)
  Image.merge("RGBA", (metal_L, zero, zero, smooth)).save(...)
  ```
- Use **`_NormalGL`** (Unity is OpenGL / Y+), not `_NormalDX`.
- Importer: normal map → `TextureImporterType.NormalMap`; packed mask → `sRGBTexture = false` **and** `alphaSource = FromInput` (otherwise the alpha — all your smoothness — is discarded); AO → `sRGB = false`.
- Tiling on ProBuilder shells (world-space auto-UVs): `textureScale = 1 / metres_per_repeat` (0.22 ≈ 4.5 m large-format slab; 0.8 ≈ 1.2 m chevron parquet).

**Pitfalls:**
- **`_GlossMapScale`**: with a `_MetallicGlossMap` assigned, Standard ignores `_Glossiness` and uses `_GlossMapScale`. Polished-stone sets have genuinely low roughness; at scale 1.0 with a reflection probe present, a marble floor becomes a black mirror of the skyline (reads as wet tarmac, albedo vanishes). Honed stone ≈ 0.35, plaster ≈ 0.45, wood ≈ 0.50.
- **Don't crush a light texture dark.** Preserving an old flat colour with `_Color = old_colour / map_mean` is right in principle, but old 0.135 over a cream marble (mean 0.70) gives tint 0.19 and the veining disappears. Pick a set whose own albedo sits near the target (e.g. a marble with mean 0.243, veins p10 0.192 → p90 0.308) and tint gently. Record `mean`, `p10`, `p90` of the Color map at extraction — they tell you whether the pattern will survive.
