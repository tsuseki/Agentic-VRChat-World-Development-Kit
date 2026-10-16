---
title: Static objects with no Bakery lightmap group selector land on a tiny 16x16 implicit lightmap
topic: lighting-baking
tags: [Bakery, BakeryLightmapGroupSelector, lightmap group, lightmapScaleOffset, orphan]
summary: In a scene with explicit Bakery groups, a ContributeGI object with no BakeryLightmapGroupSelector on itself or an ancestor drops into an implicit group that can resolve to 16x16 — lit flat or black, yet every "is it lightmapped" check passes.
---
**Symptom:** A newly added static object (even a 17 m plinth or a 13 m panel in full sun) bakes flat or near-black (0.000–0.004 sRGB). It still has a valid `lightmapIndex`, so checks pass.

**Cause:** It does not inherit a neighbour's group. Bakery puts it in an implicit group named `<SceneName>_LM0`, which can auto-resolve to **16x16**. The selector must be **on the object or an ancestor**. Classic trap: removing a child's selector "so it bakes with what it's bolted to" when the parent's selector lives on the parent's *mesh child*, not on the wrapper GameObject the child is parented under.

**Fix / rule:**
- Before removing a selector to "match the parent", read the selector off the parent's **renderer**, not its wrapper.
- Put a `BakeryLightmapGroupSelector` (field `lmgroupAsset`, type in `BakeryRuntimeAssembly`) on each new object, pointing at the group `.asset`.
- Wanting a surface near-black is not a reason to leave it orphaned — you lose sky gradient and contact AO and it reads as a hole. Darken the **material** and bake normally.
- Check group headroom first: a fixed-resolution group (e.g. 2048, `autoResolution=False`) just thins everything when you pile more area in.
- Orphaned objects still **cast** shadows normally; only what they receive is ruined. Invisible ShadowsOnly proxies can be left orphaned.

**Verify (before spending the bake):** list renderers by `lightmapIndex` and dump `LightmapSettings.lightmaps[i]` dimensions. Anything on a 16x16 map is orphaned. The tell is `lightmapScaleOffset == (1,1,0,0)` (un-atlased sentinel); properly packed objects show a fractional scale.
