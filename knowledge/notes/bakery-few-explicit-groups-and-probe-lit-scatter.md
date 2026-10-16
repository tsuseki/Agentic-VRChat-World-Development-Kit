---
title: Put every lightmapped renderer in a few explicit Bakery groups; keep scatter probe-lit with no selector
topic: lighting-baking
tags: [Bakery, BakeryLightmapGroupSelector, lightmap group, receiveGI, LightProbes, atlas]
summary: A scene of ~2600 GI renderers baked to exactly 3 atlases once every lightmapped renderer had a selector and the scatter/LOD props were switched to probe-lit with no selector.
---
**When:** large scenes with thousands of static renderers (terrain chunks, scatter, LOD'd photoscans).

**How:**
- Without a `BakeryLightmapGroupSelector`, renderers get auto-atlased into their own pages (see also [bakery-objects-without-group-selector-bake-at-16x16](bakery-objects-without-group-selector-bake-at-16x16.md)). Assign a selector to every lightmapped renderer, into a few explicit groups (e.g. Terrain 4096, Props 2048). `autoAtlas = false`. Count "ungrouped" before every bake; expect 0.
- Make scatter and LOD'd props `ReceiveGI = LightProbes` (2490 of 2626 renderers in one scene): they still cast into the lightmap but take lighting from probes, saving atlas on LODs that rarely draw. Only terrain + large built structures stay lightmapped (136 here).
- **A probe-lit renderer must not carry a selector:** a group whose members are all probe-lit still emits a full empty atlas (an unused 2048² ≈ 21 MB was baked and bound this way). Check `receiveGI` before concluding a renderer "failed" to bake.
- Settings used with normal-mapped photoscan props: `renderDirMode = DominantDirection` (they go flat with directional mode None), L1 probes, `exportTerrainTrees = false`.

**Pitfalls:**
- If group setup is done by a blunt "assign everything" script, any later hand-applied refinement (hero tiles with dense UV2, per-LOD groups, a subsurface canopy group) is **silently wiped** on the next run: the bake just reports fewer groups, finishes much faster, and density collapses (13.65 → 1.37 texels/m on the hero ground). A hero tile with full-range UV2 left in the shared terrain group gets stretched across the whole atlas. Make the setup script rebuild every refinement as its last act.
- After any group work, aggregate selectors by `lmgroupAsset.name` and compare to expected counts.
- If a game area becomes a driving surface or similar, a light probe grid over it is mandatory or dynamic objects (vehicles) render flat.
