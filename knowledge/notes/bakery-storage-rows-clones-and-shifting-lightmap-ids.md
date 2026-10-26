---
title: Bakery storage rows go stale on clones, rebuilds and probe-lit conversions, and lightmap ids renumber between bakes
topic: lighting-baking
tags: [Bakery, ftLightmapsStorage, lightmapIndex, lightmapScaleOffset, clones, lightmap groups, verification]
summary: Bakery re-applies lightmap bindings from its storage rows at load, so clones, rebuilt renderers and renderers moved to probes keep wrong lighting until rows are fixed or a bake runs; and adding or emptying a group renumbers every lightmap id, so never hard-code ids in checks.
---
**Symptom:**
- A duplicated lightmapped prop shows another place's lighting (a bright patch in shade, a shadow with no caster).
- A renderer switched to probes keeps its old lightmap after reopening the scene.
- After a builder script recreates its roots, the whole area renders unlit (`lightmapIndex -1`).
- A verification script that worked last week reports 0 of 110 renderers bound after a healthy bake.

**Cause:**
- Bakery keeps one row per baked renderer in `ftLightmapsStorage` (on `!ftraceLightmaps`) and re-applies index and scale-offset from it at load. A clone has no row; it keeps the serialized copy of its source's index and scale-offset, so it samples the source's chart until the next bake.
- A renderer moved to `receiveGI = LightProbes` still has its row, so Bakery puts the old binding back at load.
- Destroying and recreating renderers leaves rows pointing at dead objects (560 rows in one rebuild).
- Lightmap ids are assigned per bake. A new group (for example a new SSS group) adds a map and shifts the ids after it; a group whose members are all gone drops out of the list. One scene went from 13 to 17 to 16 maps over three bakes and the same suite moved from id 6 to 8.

**Fix / rule:**
- Treat clones and renderers placed since the last bake as unbaked: probe-light them or re-bake before review.
- When moving a renderer to probes, remove its storage row too (and set `lightmapIndex = -1`).
- Rebuild storage rows from the live renderers right after a bake, never from an older snapshot; write snapshots with invariant-culture numbers (a comma-decimal locale split one TSV wrongly and put garbage scale-offsets on 5,560 rows).
- Verify bindings by renderer path → "has any valid index and finite scale-offset", never by expected id numbers.

**Verify:** after save, close and reopen: count lightmapped receivers with a valid index, finite scale-offset and a storage row; count rows whose renderer is null; the storage `maps` length equals the live lightmap count.
