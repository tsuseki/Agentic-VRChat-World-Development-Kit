---
title: Merge terrain scatter into per-cell meshes, and delete what players cannot see
topic: performance
tags: [terrain trees, impostor, detail grass, merged mesh, LODGroup, CPU]
summary: Unity terrain trees with LODGroup prefabs and the detail-grass system cost ~9 ms and ~15 ms of CPU respectively; bake scatter into merged per-cell meshes and remove sub-pixel geometry.
---
**Symptom:** low FPS in a large outdoor world on weak PCs; the suspected "detailed props" measure cheap (here ship + furniture ≈ 0.7 ms GPU / 0.3 ms CPU).

**Cause (measured):**
- Unity terrain trees using LODGroup prefabs get per-instance main-thread cull/LOD work every frame: ~9 ms CPU (`Camera.Render` 14 → 5 ms with `treeDistance = 0`) + ~7.5 ms GPU at 34k instances, even though each impostor was only 6 tris. 34k tiny alpha-tested `Cull Off` billboards also quad-overshade the GPU.
- Terrain detail grass: ~15.6 ms CPU + 7.8 ms GPU for tufts nobody could see from the play altitude.

**Fix / rule:**
- Bake terrain-level geometry (trees, rocks, bushes, future props) into **merged meshes per spatial cell** (e.g. 250 m cells, one object per cell, own layer, per-layer cull distance). Keep `treeDistance` / `detailObjectDistance` at 0; add instances to the source data and re-run the cell bake.
- Judge visibility from the **real player viewpoints** (e.g. deck altitude), not from ground level. If something reads as a few pixels from there, delete it instead of optimizing it.
- Static occlusion culling is incompatible with geometry that moves at runtime (e.g. sliding/streamed terrain blocks); keep it off there.

See also [distance-weighted-scatter-in-a-spatial-grid](distance-weighted-scatter-in-a-spatial-grid.md).
