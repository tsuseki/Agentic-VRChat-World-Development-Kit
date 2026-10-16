---
title: Fit building box colliders to the area-weighted 90th-percentile wall plane
topic: colliders-physics
tags: [BoxCollider, facade, percentile, mesh triangles, house]
summary: Replace per-building MeshColliders with one box whose faces sit on the area-weighted 90th percentile of outward wall triangles; vertex-based trims land on window boxes instead.
---
**When:** replacing MeshColliders on detailed buildings (window boxes, shutters, eaves, jettied upper storeys) with one `BoxCollider` each. One town went from ~722k live collider triangles to ~1.9k this way.

**How:**
- For each of the 4 side faces, take triangles in a y 0.3–2.2 m band whose local normal component on that axis is > 0.6.
- Weight each by **triangle area**, coordinate = centroid; take the **90th percentile**, add 2 cm margin. Box Y spans the full mesh height.
- Safety rails: only ever **shrink** a face, cap the pull at 1 m, require ≥ 0.8 m² of facing area, abort if a box would lose > 50 % of an axis.
- Result: every box within ~9 cm of its outermost wall plane; small window hoods poke through, as intended.

**Pitfalls:**
- Raw mesh/renderer extent includes eaves and overhangs → invisible walls.
- Percentile trim of **vertex** positions fails: trim pieces carry far more vertices per m² than flat wall, so the face lands on them (here 41 of 108 houses ended 0.25–0.38 m proud). Vertex density ≠ surface area.
- Archways / gatehouses whose footprint is mostly open ground (e.g. 180 m² bulge vs 24 m² of wall) must never get one solid box.
- A single ground box can replace a flat floor MeshCollider: size the slab so its top lands exactly at the paving height.

**Verify:** capsule flood-fill before/after — see [verify-collision-with-capsule-flood-fill](verify-collision-with-capsule-flood-fill.md).
