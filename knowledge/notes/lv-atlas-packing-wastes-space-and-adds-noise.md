---
title: Light Volume atlas packing wastes 30-45 % and swings VRAM by about 1 MB between similar layouts
topic: performance
tags: [VRC Light Volumes, atlas, packing, VRAM, voxels]
summary: The Light Volume atlas costs voxels × 24 B, but the package's greedy packer leaves the 3D atlas only 55-73 % full, so fitting volumes tighter saves far less than the voxels removed and similar layouts differ by about ±1 MB.
---
**Symptom:** Fitting volumes tightly cut the covered voxels by 40 % (4 → 32 boxes over the same trees) but the atlas VRAM moved only 9.7 → 6.6 MB, and neighbouring box counts jumped up and down by about 1 MB.

**Cause:** VRAM = atlas width × height × depth × 24 B (three RGBAHalf 3D textures, 8 B per voxel each). The package (`Texture3DAtlasGenerator.PackTextureBlocks`) packs greedily: blocks sorted by volume, placed at corner candidates, 1-voxel padding, no rotation, first result kept. A 50-room atlas (102×32×816) was 55 % full; adding volumes only filled the existing gaps until the atlas had to grow along an axis.

**Rule:** When choosing a volume layout, read the generated atlas size, never sum box volumes. Treat differences under ~1 MB between layouts as packing luck. Per-room volumes whose sizes stack well (shared heights) waste less.

**Verify:** Re-run the packer outside Unity on the real block list (the package's code in a small console harness reproduced the scene atlas exactly: 102×32×816, 150 placements) before and after a layout change.

Related: [lightmap-vs-light-volume-is-a-per-object-test](lightmap-vs-light-volume-is-a-per-object-test.md)
