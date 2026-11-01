---
title: A lightmap group's atlas size drives upload size; size it from the texels it needs
topic: lighting-baking
tags: [atlas size, bundle size, texel density, lightmap groups]
summary: Size a lightmap group's atlas from the summed chart texels it actually needs: an 8192 group holding 17.1 M needed texels in 67 M allocated cost ~47 MB of upload against 4096.
---
**Symptom:** a world's scene bundle was 224.3 MB; its trees group baked to 8192² (67 M texels allocated) for 17.1 M
texels of charts.

**Fix / rule:** before choosing a fixed group resolution, sum the chart rects the group needs (texels per chart from
`lightmapScaleOffset` × atlas size, or from the pre-bake density plan) and pick the smallest atlas set that holds them
at the target density. With 4096² and world-owned group copies the bundle was 177.3 MB.

**Pitfalls:** with shared LOD UVs the far LODs give no texels back (see Related), so atlas size is the only density
lever and halving it visibly weakens canopy self-shadowing; judge that with lightmap-only renders.

**Related:** [bake-shared-lod-uv-leaves-atlas-size-as-the-only-lever](bake-shared-lod-uv-leaves-atlas-size-as-the-only-lever.md).
