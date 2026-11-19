---
title: Repack shipped lightmaps tightly and drop empty ones before upload
topic: performance
tags: [lightmap, Bakery, atlas, VRAM, packing, upload]
summary: A shipped 4096 garden lightmap was about half empty and an unused group still shipped its own lightmap; tight repacking at the same texel density and deleting empty atlases saved about 9 MB with no visible change and no re-bake of the look.
---
**Symptom:** The biggest exterior lightmap of a finished world was 4096² (16.8 MB BC6H), and a probe-lit tower group still shipped a 1024² lightmap that no renderer referenced.

**Cause:** Bakery sizes an atlas to the next allowed resolution and leaves the rest empty; a group whose members were all moved to probes still bakes and ships an empty atlas.

**Fix / rule:** At the end of a world (and after any change that moves renderers off a lightmap):
1. Count renderers per `lightmapIndex`; delete any lightmap with 0 users and stop its group from baking (one empty atlas = 2.1 MB here; 16 → 15 lightmaps, every renderer kept its texture).
2. Repack each big atlas tightly at the same texel density (xatlas-style packer, padding 3, no hole fill): the 4096 exterior fit in 3072 (9.4 MB, −7.3 MB).

**Verify:** Same-camera lightmap-only renders before and after (see `bake-compare-bakes-with-lightmap-only-renders`); per-renderer texel density ratio ~1.00; preview each atlas to check tile fill.

**Pitfalls:** A partial or group bake can also resize other atlases (a tower atlas went 1024 → 2048 in an exterior-only experiment). In experiments bake only the group under test, or restore the other lightmap files before measuring memory.
