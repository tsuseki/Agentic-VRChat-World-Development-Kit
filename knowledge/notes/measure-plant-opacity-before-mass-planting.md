---
title: Measure plant silhouette opacity before choosing a species for mass planting
topic: placement-layout-design
tags: [vegetation, planting, opacity, coverage, Poly Haven, decimate, triangles]
summary: Scanned shrubs can be ~5% opaque and broadleaf ~25-30%; no achievable count of a sparse plant hides the ground, so pick the mass species by measured cover per 1k tris.
---
**Symptom:** Planting 878, then 1155, then 3243 shrubs moved visible bare soil 87.3% -> 79.6% -> 80.7%. Adding 2000 plants changed nothing: the signature of a wrong species, not a wrong count.

**How (measurement):** Park a rig in empty air (e.g. y = 200), put a keyed backdrop quad behind it, scale one specimen to exactly 1 m tall, render it head-on, and compute `1 - (backdrop pixels inside the specimen's bounding rect / rect area)`.

Measured (normalised to 1 m tall):

| species | opacity | tris | cover per 1k tris |
|---|---|---|---|
| Dracaena (broadleaf) | 29.2% | 2394 | 12.2 |
| Strelitzia | 19.7% | 5486 | 3.6 |
| ice plant | 13.3% | 425 | 31.2 |
| Poly Haven `shrub_01..04` | 4.4-8.2% | 177-716 | 18-44 |
| Poly Haven `grass_medium_01` (tiny) | 7.3% | 34 | 214 |

Scanned shrubs are accent specimens: beautiful alone, useless as mass. At 5% opacity ~32 overlapping layers are needed to hide 80% of the ground.

**Rules:**
- Pick the mass species by **cover per 1k tris**, not by looks or name.
- **Decimate first, then measure.** Dracaena 2394 -> 822 tris kept 24.7% of its 29.2% opacity; cover per 1k tris went 12.2 -> 30.
- Broadleaf carries wide beds seen from above; fine species suit narrow runs seen edge-on. Removing broadleaf from narrow beds entirely cost coverage until a minority share went back in.
- Beds seen at a steeper angle need more: at 1.6 m eye height low beds needed ~0.185 m spacing where waist-high runs were fine at 0.22 m.

Related: [measure-canopy-coverage-not-plant-density](measure-canopy-coverage-not-plant-density.md), [scatter-to-the-container-edge](scatter-to-the-container-edge.md).
