---
title: Non-power-of-two textures silently lose aspect ratio or compression — import with npotScale = ToLarger
topic: materials-textures-shaders
tags: [NPOT, texture import, npotScale, DXT, BC, mipmaps, VRAM, aspect ratio, picture frames, wall-art]
summary: npotScale=ToNearest rounds each axis independently (stored aspect changes), and NPOT + mipmaps blocks DXT (RGB24 at ~9x VRAM); any POT rescale compresses, and the quad — sized from the source file's aspect, never from Texture.width/height — stretches it back.
---
**Symptom:** Imported artwork/screenshots look squashed, hung pictures are stretched, or a memory audit finds uncompressed RGB24 textures that imported "successfully" with `Compressed` set and dimensions divisible by 4. Example: 180 art textures = 1435 MB VRAM, 117 of them uncompressed.

**Cause:**
1. `npotScale = ToNearest` rounds **each axis independently**: 2432 × 1664 (1.46:1) → 1024 × 512 (2.0:1); 957 × 364 (2.63) → 1024 × 512 (2.00); 990 × 1107 → 1024 × 1024. No warning. The image still displays correctly on a quad that has the *source* aspect with 0–1 UVs, but anything that reads `Texture.width/height` to size or fit a frame gets the wrong shape, and the squash gets blamed on the source art. `maxTextureSize` clamps those dimensions further.
2. NPOT + mipmaps blocks DXT: at 1280 × 720, mips off → DXT1 900 KB; mips on → **RGB24 8400 KB**. Divisible-by-4 is not sufficient, and an explicit platform override is **silently ignored**:
   ```csharp
   var ps = ti.GetPlatformTextureSettings("Standalone");
   ps.overridden = true; ps.format = TextureImporterFormat.DXT1;
   ti.SetPlatformTextureSettings(ps); ti.SaveAndReimport();
   // texture.format is STILL RGB24, no warning
   ```
3. `npotScale = None` keeps aspect, but BC needs multiples of 4 down the mip chain: 1024 × 576 mips down to 16 × 9, and 9 isn't, so the whole texture drops to uncompressed.

**Fix / rule:** any POT rescale restores compression; use `npotScale = ToLarger`, which rounds both axes **up** to the same POT square (1920 × 1080 → 2048 × 2048 → clamped by `maxTextureSize` to 1024 × 1024), DXT1 with full mips:
```csharp
ti.npotScale          = TextureImporterNPOTScale.ToLarger;
ti.maxTextureSize     = 1024;
ti.textureCompression = TextureImporterCompression.Compressed;
ti.mipmapEnabled      = true;
ti.SaveAndReimport();
```
Hang it on a quad with the real aspect (e.g. 1.778:1) and plain 0–1 UVs — correct on-screen proportions; no letterbox padding or UV cropping needed. Source file stays untouched. Verified on 18 wall-art images: ToNearest → 1024×512 stored squashed; None → correct but RGB24 (25 MB total); ToLarger → 1024² DXT1. An earlier ToNearest pass on 180 images also compressed (2048×1152 RGB24 21.00 MB → DXT1 0.67 MB; set 1435 MB → 170 MB) but left the stored aspect wrong, which is why ToLarger replaces it. ToNearest stays acceptable only where nothing reads the texture's dimensions (e.g. a card that is Blit-rescaled into a RenderTexture).

- **Size frames from the file on disk** (e.g. PIL `Image.open(p).size`), never from `Texture2D.width/height`; record the source aspect somewhere other than the imported texture. If the frame mesh has a fixed picture area (e.g. exactly 16:9), apply the aspect via non-uniform scale on the instance.
- **Choose `maxTextureSize` by px per metre:** `texture.width / renderer.bounds` width. ~450–500 px/m is comfortable for wall art; below ~320 px/m reads soft. Text-heavy images are the strictest test.
- **Batch caveat:** reimporting ~180 textures exceeds a typical MCP call timeout; the call may report an unknown outcome while the editor keeps working. Wait ~90 s and re-query memory instead of re-running the batch.

**Pitfalls:** if you instead store a pre-squashed square file on disk, it looks broken and invites someone to "fix" it, reintroducing both bugs — leave a note next to it.

**Verify:** `texture.format` and `Profiler.GetRuntimeMemorySizeLong(tex)` after reimport (or the resolved platform format in the Inspector footer), count remaining NPOT textures, and compare each placed picture's world aspect against the source pixel aspect (assert 0.00% error).
