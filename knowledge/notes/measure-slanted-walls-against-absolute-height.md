---
title: Measure slanted walls against absolute height, not floor-relative height
topic: colliders-physics
tags: [collider, slanted wall, hull, probe, raycast, measurement]
summary: Probing a flared wall at floor+1 m on a floor that changes level fakes a taper; probe at fixed absolute y and fit the wall plane.
---
**Symptom:** wall probes report the room narrowing toward one end (e.g. ±2.02 m vs ±1.88 m), so you build a stepped multi-box taper.

**Cause:** the walls flare outward (~20°, plane `x = ±(a + b·y)`) and the floor at that end is lower (0.43 m here). A probe at "floor + 1 m" is simply lower on the same slope. The room doesn't narrow at all.

**Fix / rule:**
- Measure wall x against **absolute y** at several heights and fit the plane; then build the collider on that plane (a rotated box).
- Fit vaulted ceilings the same way (e.g. `y = 2.14 − 0.52·|x|`).
- A pointed (chevron) end wall is two facets: one flat box across it sits well off the glass at the corners (23 cm here). Use one box per facet.
- Keep collider roots at identity transform and unit scale.
