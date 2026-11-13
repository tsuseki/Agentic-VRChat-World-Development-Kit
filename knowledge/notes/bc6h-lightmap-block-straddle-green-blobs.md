---
title: BC6H lightmap blocks straddling a bright and a dark chart turn the bright texels green
topic: lighting-baking
tags: [bc6h, lightmap compression, chroma, soft goods, bakery]
summary: Coloured blobs on bright cushions that survive re-bakes can come from BC6H compression, not the bake; equalise chroma per chart inside each 4x4 block (luminance kept) instead of re-baking.
---

**Symptom.** Green or pink blobs on white cushion lightmaps, visible from standing eye height. Three re-bakes with
more GI samples and more texels each cleaned some pieces and added blobs on others. A bake-noise chroma median
filter didn't touch them.

**Cause.** The baked `.hdr` texels at a blob were neutral, but the BC6H-compressed lightmap decoded them green
(R/Y 0.58, G/Y 1.14). A 4x4 BC6H block straddled a bright cushion chart and a nearly black neighbour chart
(luminance about 0.01) whose texels had junk chroma (R/Y 4.7, G/Y 0). The block endpoints fit the junk, which tints
the bright texels. Re-bakes move chart packing, so the blobs move. An uncompressed RGBAHalf override removes them but
costs about 56 MB per 4K pair; `compressionQuality` 100 changes nothing.

**Fix.** Post-process the lightmap source `.hdr` before import:
- Build a texel mask per renderer and UV2 chart from `lightmapScaleOffset`.
- Inside each 4x4 block, give each chart's texels one luminance-weighted chroma, keeping each texel's luminance exactly.
- Leave texels that would change by under 1 % at their baked bytes.
- Re-run after every re-bake of those groups.

**Verify.**
- Do a closed-loop BC6H round-trip of the fixed atlas.
- Diff the whole atlas: 0 texels changed outside the mask, small luminance change inside.
- Take same-camera before/after shots at the blob poses.
