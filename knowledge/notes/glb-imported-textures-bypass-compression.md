---
title: glTFast .glb sub-asset textures ship uncompressed — never ship GLBs as-is
topic: performance
tags: [glb, glTFast, texture compression, VRAM, Tripo, import]
summary: Textures embedded in .glb files imported by glTFast bypass TextureImporter compression (RGB24 2048² ≈ 37 MB each); re-encode or delete them.
---
**Symptom:** huge texture memory from a handful of AI-generated or downloaded `.glb` models.

**Cause:** glTFast imports GLB textures as sub-assets that bypass the TextureImporter: uncompressed RGB24 (2048² ≈ 37 MB each), plus readable CPU copies, some without mips.

**Fix / rule:** don't leave GLBs as shipping assets. Convert the model (e.g. via Blender to FBX + separate texture files) so textures import compressed, or delete the GLB. Deleting 12 generated GLBs took referenced texture memory 2124 → 574 MB in one world.
