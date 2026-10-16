---
title: Measure texel density per triangle as sqrt(worldArea/uvArea); never derive it from UV span
topic: geometry-meshes-uvs
tags: [texel density, UV, smart_project, tiling, moire, aliasing, Blender]
summary: Comparing a mesh's UV bounding span to its size is not a measurement (off by 3.3x on packed islands); sum world and UV triangle areas instead, and re-measure after every geometry edit.
---
**Symptom:** Tyres reported at "~0.26 m per tile" render with ~15 cm rubber grain and get called "stacked millstones"; real density was 0.854 m per tile.

**Cause:** `smart_project` packs many small islands into 0..1 with margins, so whole-mesh UV span has no fixed relation to surface distance. A build-script `uv_scale` applied after smart_project (e.g. `k = max(ob.dimensions) / uv_scale; uv *= k`) is therefore **not** metres-per-tile despite what its comment says; the factor is per-prop and changes when topology changes (adding two profile points moved a predicted 0.259 to an actual 0.387).

**Fix / rule:**
- Measure: sum world triangle area and UV triangle area over the mesh → `sqrt(worldArea / uvArea)` = metres per texture tile.
- Density is linear in the scale factor, so one measurement solves it: `new = old * (target / measured)`. Re-measure after ANY geometry edit; never chain a solve off a pre-edit measurement.
- A per-object UV scale can't give per-material tiling on multi-material props — set `_MainTex` / `_BumpMap` tiling on the Unity material instead, and make sure any regeneration script doesn't overwrite it.
- Aliasing/moiré on a large flat surface is a **frequency** problem, not filtering: a 1673 m² roof at 6.6 cm rib pitch ignored aniso 8 + trilinear; retiling to a 25 cm pitch fixed it. Check detail pitch in world metres before touching importer settings.
