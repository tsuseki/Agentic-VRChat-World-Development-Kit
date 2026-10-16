---
title: Unity will not compress non-power-of-two textures; npotScale ToNearest fixes it
topic: performance
tags: [texture-compression, npot, dxt, vram, wall-art, importer]
summary: Unity silently refuses BC/DXT compression on non-power-of-two textures even with an explicit format override; setting npotScale to ToNearest fixes it without visible distortion.
---
**Symptom:** A folder of photos/artwork shows `Compressed` in the importer, dimensions divisible by 4, yet runtime format is `RGB24`. Example: 180 art textures = 1435 MB VRAM, 117 uncompressed.

**Cause:** Dimensions were non-power-of-two (e.g. 2048x1152). Divisible-by-4 is not sufficient - the importer wants POT for BC/DXT on Standalone. An explicit platform override is **silently ignored**:
```csharp
var ps = ti.GetPlatformTextureSettings("Standalone");
ps.overridden = true; ps.format = TextureImporterFormat.DXT1;
ti.SetPlatformTextureSettings(ps); ti.SaveAndReimport();
// texture.format is STILL RGB24, no warning
```

**Fix / rule:**
```csharp
ti.npotScale          = TextureImporterNPOTScale.ToNearest;   // the actual fix
ti.maxTextureSize     = 1024;
ti.textureCompression = TextureImporterCompression.Compressed;
ti.mipmapEnabled      = true;
ti.SaveAndReimport();
```
Sample: RGB24 2048x1152 = 21.00 MB -> DXT1 1024x512 = 0.67 MB. Whole set: 1435 MB -> 170 MB.

- **`npotScale` does not distort the picture.** It resamples into a POT container (2048x1152 -> 2048x1024), but the quad still maps UV 0..1 across its own 16:9 face, so the image displays undistorted (A/B render confirmed). Only vertical resolution is lost. Don't bother with letterbox padding + UV cropping.
- **Choose `maxTextureSize` by px per metre:** `texture.width / renderer.bounds` width. ~450-500 px/m is comfortable for wall art; below ~320 px/m reads soft. Text-heavy images are the strictest test.
- **Batch caveat:** reimporting ~180 textures exceeds a typical MCP call timeout; the call may report an unknown outcome while the editor keeps working. Wait ~90 s and re-query memory instead of re-running the batch.
- **Prefer `ToLarger` today.** `ToNearest` rounds each axis independently, which changes the stored aspect for anything that reads `Texture.width/height`; any POT rescale compresses. See [npot-textures-lose-aspect-and-compression](npot-textures-lose-aspect-and-compression.md), which supersedes the importer choice above.

**Verify:** `Profiler.GetRuntimeMemorySizeLong(tex)` and `texture.format` after reimport; count remaining NPOT textures.
