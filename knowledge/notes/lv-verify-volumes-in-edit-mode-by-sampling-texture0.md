---
title: Prove Light Volume shade in edit mode by sampling the volume texture
topic: probes-reflection-and-light
tags: [VRC Light Volumes, Texture3D, verification, tree shade, light probes]
summary: A baked volume's Texture0 is a readable RGBAHalf Texture3D; GetPixelBilinear at under-crown, shade-side and open-sun points proves baked shade without play mode, and showed volumes carry tree shade that light probes miss.
---
**When:** checking that baked volumes carry shade (under trees, under roofs) without entering play mode, where edit mode
pushes no volume globals to shaders.

**How:** for each volume, map world points into its local 0–1 box and read `Texture0.GetPixelBilinear(u, v, w)` (L0) at
an under-crown point, a point beside the tree on the shade side, and an open-sun point.

**Result in one world:** under-crown points read 0.02–0.57 of open sun; light probes under the same crowns read ~1.2 in
most places, so probes ignore baked tree shade and volumes don't. Lightmap comparison was rough (3 of 7 trees sampled
cleanly; two disagreed by 2–4×).

**Verify:** the shade/sun ratios per sampled tree in the bake report, then the play-mode sphere test in
`vrc-light-volumes-traps` for avatars.
