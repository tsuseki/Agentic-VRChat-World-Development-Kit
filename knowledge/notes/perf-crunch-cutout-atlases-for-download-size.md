---
title: Crunch is the download-size lever for big cutout atlases; quality barely changes size
topic: performance
tags: [crunch, DXT5, texture compression, bundle size, foliage atlas]
summary: The upload limit is download size, so crunching large foliage atlases is the budget lever (58 → ~15 MB); crunch quality hardly changes size, so use 95, on world-owned copies with fresh GUIDs.
---
**Symptom:** a world over the upload guidance carried 58 MB of BC7 planting atlases.

**Cause:** crunch shrinks the download, not VRAM, but the limit that bit was download size.

**Fix / rule:** world-owned copies of the atlases (fresh GUIDs, originals untouched), DXT5 crunched, 2048², Alpha Is
Transparency, swapped in by material copies (here 44,379 renderer slots); ~58 → ~15 MB. Quality 70 → 85 added only
0.6 MB because the codebook dominates, and q70 showed a faint dotted artefact at a cutout edge in one pose: use 95.

**Pitfalls:** source PNG copies added ~85 MB to the repo; the GPU still decompresses to full DXT5 size.

**Verify:** bundle-size A/B, then native-resolution crops of cutout edges at the closest player distance.
