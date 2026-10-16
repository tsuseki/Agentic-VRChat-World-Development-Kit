---
title: Bakery silently skips LODGroup renderers unless each LOD level has its own lightmap group
topic: lighting-baking
tags: [Bakery, LODGroup, sceneLodLevel, lightmap group, BakeryLightmapGroupSelector]
summary: Renderers under a LODGroup are not baked by Bakery when their lightmap group has sceneLodLevel = -1; create one group per LOD level.
---
**Symptom:** You set ContributeGI and a lightmap group selector on LOD props, bake, and they stay probe-lit (`lightmapIndex 65534`). No warning, no console error.

**Cause:** Bakery does not bake any renderer belonging to a `LODGroup` if its lightmap group has `sceneLodLevel = -1` (the default).

**Fix / rule:** One lightmap group **per LOD level**, each with `sceneLodLevel` set to that level, and each LOD renderer's `BakeryLightmapGroupSelector.lmgroupAsset` pointing at the matching group:
```
LMGroup_PropsLOD0.asset  sceneLodLevel = 0   <- *_LOD0 renderers
LMGroup_PropsLOD1.asset  sceneLodLevel = 1   <- *_LOD1 renderers
LMGroup_PropsLOD2.asset  sceneLodLevel = 2   <- *_LOD2 renderers
```
New group assets need a unique `id` and `sortingID`; colliding with an existing group makes the bake output confusing. Non-LOD renderers stay in the plain group.

**Pitfalls:** Do not "fix" it by baking LOD0 only. On typical Poly Haven props LOD0 drops out at about 3 m, so LOD1 is what players see most of the time, and you will photograph the unbaked LOD.

**Verify:** Group renderers by name suffix and count lightmapped vs not. A clean split like `base: 135 lightmapped / *_LOD0: 0 / *_LOD1: 0 / *_LOD2: 0` is this bug, not an atlas or UV2 problem.
