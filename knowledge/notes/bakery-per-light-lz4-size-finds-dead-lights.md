---
title: Bakery's per-light lz4 file size reveals lights that baked pure black
topic: lighting-baking
tags: [Bakery, frender, lz4, dead light, emitter, diagnostics]
summary: Each Bakery light writes light_<n>_1_HDR.lz4 into %TEMP%/frender; many lights sharing one identical small size means they baked black.
---
**When:** A room looks under-lit after a Bakery bake, every light component looks healthy in the inspector, and confirming which emitter did nothing would otherwise mean sampling the baked atlas through each renderer's `lightmapScaleOffset`.

**How:** During a bake, each light's own contribution lands in `%TEMP%\frender\light_<n>_1_HDR.lz4` (`Path.Combine(Environment.GetEnvironmentVariable("TEMP"), "frender")`). An all-black light compresses to a constant size. In one measured scene every dead light was exactly 93,451 bytes; working accent lights were 180-230 KB, a working slab emitter 1.12 MB. A light at ~96 KB against that baseline was essentially black, and pointed at the real cause before any pixel was measured.

List the folder after a bake. The giveaway is many lights sharing one *identical* size while working lights all differ. Map a file back to its source light by mtime and the `lights<N>` label Bakery prints.

**Pitfalls:**
- The baseline size depends on lightmap group resolution, so capture it from your own scene's bake; there is no universal number.
- It tells black from non-black, not bright from dim. lz4 size tracks pattern entropy, so do not use it as a brightness scale or to compare two working lights.
