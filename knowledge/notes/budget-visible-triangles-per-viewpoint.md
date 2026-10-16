---
title: Budget triangles visible per viewpoint, not per scene
topic: performance
tags: [triangle-budget, occlusion-culling, lod, sightlines, pc-performance]
summary: What hurts VRChat PC performance is what the camera renders per frame, so set a ceiling on triangles visible from any player viewpoint (around 3 million is a reasonable upper limit) and enforce it with culling, LODs and sightline breaks.
---
**When:** Planning or reviewing any area of a world, especially long halls, balconies overlooking a full hall, and views between separate zones.

**How:**
- Budget per viewpoint, not per scene: check worst-case sightlines. Treat roughly 3 M visible triangles from any player position as an upper limit (a recommended ceiling, tune to your audience).
- Enforce with: baked occlusion culling before publish, camera far clip, `LODGroup`s on dense props, walls/seals that block sightlines between zones (keep naturally partitioned areas partitioned).
- Decimate heavy instanced props (LOD swaps on repeated light fixtures saved ~950k tris in one world) rather than accepting the cost. Long draw distances on scattered vegetation are a common cause of severe lag.

**Verify:** during every area review, sample visible triangles from representative viewpoints - Game view stats, or a script summing triangles of renderers whose bounds intersect the camera frustum within far clip (approximate is fine). See [measure-editor-fps-and-tris-via-unitystats](measure-editor-fps-and-tris-via-unitystats.md) and [census-tris-per-source-asset](census-tris-per-source-asset.md).
