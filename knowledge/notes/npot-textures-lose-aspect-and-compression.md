---
title: Non-power-of-two textures silently lose aspect ratio or compression — import with npotScale = ToLarger
topic: materials-textures-shaders
tags: [NPOT, texture import, npotScale, DXT, BC, mipmaps, VRAM, aspect ratio]
summary: npotScale=ToNearest rounds each axis independently (stored aspect changes), and NPOT + mipmaps blocks DXT (RGB24 at ~9x VRAM); any POT rescale compresses, and the quad — sized from the source aspect, never from Texture.width/height — stretches it back.
---
**Symptom:** Imported artwork/screenshots look squashed, or a memory audit finds uncompressed RGB24 textures that imported "successfully".

**Cause:**
1. Default `npotScale = ToNearest` rounds **each axis independently**: 2432 × 1664 (1.46:1) → 1024 × 512 (2.0:1). No warning. The image still displays correctly on a quad that has the *source* aspect with 0–1 UVs, but anything that reads `Texture.width/height` to size or fit a frame (e.g. driving a canvas from its texture's aspect) gets the wrong shape, and the squash gets blamed on the source art.
2. NPOT + mipmaps blocks DXT: at 1280 × 720, mips off → DXT1 900 KB; mips on → **RGB24 8400 KB**.
3. `npotScale = None` keeps aspect, but BC needs multiples of 4 down the mip chain: 1024 × 576 mips down to 16 × 9, and 9 isn't, so the whole texture drops to uncompressed.

**Fix / rule:** any POT rescale restores compression. Recommended: `npotScale = ToLarger`, which rounds both axes **up** to the same POT square (1920 × 1080 → 2048 × 2048 → clamped by `maxTextureSize` to 1024 × 1024), DXT1 with full mips. Hang it on a quad with the real aspect (e.g. 1.778:1) and plain 0–1 UVs — correct on-screen proportions. Source file stays untouched. Verified on 18 wall-art images: ToNearest → 1024×512 stored squashed; None → correct but RGB24 (25 MB total); ToLarger → 1024² DXT1. Either way, record the source aspect somewhere other than the imported texture dimensions. See also [npot-textures-cannot-be-compressed](npot-textures-cannot-be-compressed.md).

**Pitfalls:** if you instead store a pre-squashed square file on disk, it looks broken and invites someone to "fix" it, reintroducing both bugs — leave a note next to it.

**Verify:** compare `Texture.width/height` to the file on disk, and check the resolved platform format (`GetPlatformTextureSettings` / Inspector footer) is actually compressed.
