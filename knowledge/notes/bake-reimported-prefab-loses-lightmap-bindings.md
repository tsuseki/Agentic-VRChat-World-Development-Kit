---
title: Re-importing a prefab family unbinds every instance's lightmap until the next bake
topic: lighting-baking
tags: [re-import, prefab, lightmapIndex, bindings, LOD]
summary: A re-imported model family gets new LOD child IDs, so every placed instance loses its baked lightmap binding (lightmapIndex < 0) until a re-bake; count unbound renderers under the family after any re-import.
---
**Symptom:** after a tree family was re-imported with fixed geometry, 78 of its renderers in the world rendered
probe-lit/unbaked.

**Cause:** the re-import generated new LOD child objects; the bake's storage rows referenced the old ones, so
`lightmapIndex` reads < 0 on the new children.

**Fix / rule:** after any re-import of a placed family, count renderers under it with `lightmapIndex < 0`; a non-zero
count means a re-bake (at least of that family's group) before the world ships. After the re-bake: 0 of 117 unbound.

**Verify:** the unbound count before and after, quoted in the bake report.
