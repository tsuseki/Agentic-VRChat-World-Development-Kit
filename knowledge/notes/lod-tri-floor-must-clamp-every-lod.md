---
title: A per-prop triangle floor must clamp every LOD, and check which LOD is on screen
topic: geometry-meshes-uvs
tags: [LOD, LODGroup, decimation, triangle budget, screenshots, surface area]
summary: LOD ratios multiply straight through a floor applied only to LOD0, and LOD0 on small props stops rendering a few metres out — so the broken LOD is what every screenshot shows.
---
**Symptom:** A thin-walled crate rebuilt with a higher budget looks unchanged; it still renders as a bare rim. Investigation drifts to materials, alpha cutout and submeshes.

**Cause:** LOD1/LOD2 were derived as `target * [1.0, 0.40, 0.15]`. A minimum floored only `target`, so the floor of 1600 gave 1600 / 640 / 240 — and 240 tris of collapse decimation on an open container is a rim. LOD0 on a 0.5 m prop stops rendering at ~2.9 m (`screenRelativeTransitionHeight` 0.15), so every screenshot was taken past LOD0.

**Fix / rule:**
- Clamp inside the LOD loop: `max(24, floor, int(target * ratio))`.
- When a prop looks unchanged after a rebuild, check which LOD is on screen: `LODGroup.GetLODs()` tri counts per level, switch distance ≈ `size / (2 * screenRelativeTransitionHeight * tan(fov/2))`. Screenshot from inside the LOD0 distance to compare like with like.
- Equal LODs are the right answer for open shells — no budget makes a rim read as a crate.
- A fix applied at one point in a derived chain gets undone downstream; check the whole chain.

**Verify:** judge completeness by **surface area**, not tri count: sum triangle areas and compare to a solid box of the same bounds. A healthy thin-walled container reads ~150% of the box's wall area (two sides per wall); a collapsed one far under 100%.
