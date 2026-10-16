---
title: Scatter vegetation by distance to the play path, emitted into a grid of merged meshes
topic: placement-layout-design
tags: [scatter, vegetation, procedural, merged mesh, frustum culling, density]
summary: Uniform scatter over a huge map reads as a few specks; weight acceptance by distance to the road with a noise mask, and merge into a spatial grid so culling still works.
---
**Symptom:** 300 cacti spread evenly over 9 km² = one plant per 90 m, which reads as three specks.

**How (working recipe):**
- Acceptance probability `1 − 0.88 · smoothstep(160, 900, dist_to_road)` multiplied by a fractal-noise thicket mask.
- Caps used: 1200 large plants / 6500 bushes / 1600 litter rocks over 9 km².
- Emit into a **6×6 spatial grid of merged meshes** (one mesh per cell per material) so frustum culling still works; never one renderer per instance, never one mesh for the whole map.
- Small-scale props such as grass tufts: combine into chunks (e.g. 16 m cells), denser around building perimeters and sparse "weeds" at street level. Blockers = building/prop renderer AABBs. Keep the seed so it can be regenerated.

**Pitfalls:** combining meshes carries each source tuft's 0–1 UV2 through → overlapping lightmap charts. Force `Unwrapping.GenerateSecondaryUVSet` on every combined mesh (and don't skip meshes that "already have UV2").
