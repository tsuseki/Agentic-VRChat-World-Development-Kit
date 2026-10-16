---
title: Measure undressed wall with props overlapping an eye-height wall band
topic: placement-layout-design
tags: [set-dressing, bare-walls, measurement, bounds, room-layout]
summary: Prop density, room-AABB edge runs and point probes all overreport bare wall by up to 10x; only projecting props that intersect an eye-height band on each real wall gives an honest number.
---
**When:** "The rooms look empty, fill the bare walls" needs a number and a location.

**Methods that failed on the same scene:**

| Method | Answer | Failure |
|---|---|---|
| Props per m2 of floor, per room | density figures | Density is not location - says nothing about *which* wall is bare |
| Bare runs along each room AABB edge | 160 m in 33 runs | Counts open edges, doorways and glazing as wall |
| Same, gated on a solid wall behind, one point sample 0.55 m into the room | 101 m + 59 m | Sideboards and wall art stand only 0.3-0.5 m deep, so they never registered; single sample height missed the upper floor |
| **Props overlapped onto a wall band** | **16.5 m** in 5 runs | correct |

**How:**
```
for each room:
  for each wall plane (the room's four AABB edges):
    require a structural wall volume within ~0.3 m behind it, else skip (glazing/open)
    build a BAND on that wall: full run length x eye height (about floor+0.9 .. floor+2.2)
    project every renderer onto the wall's along-axis, keeping only those whose
      bounds INTERSECT the band (inward depth up to ~0.6 m, not a point sample)
    subtract the occupied intervals from the run; report gaps >= 3 m
```

**Pitfalls:**
- A wall is never an obstruction for its own cladding: exclude partition/shell/slab meshes from the occupancy set or every wall reports itself dressed.
- Report each run's world coordinates (room, along-axis, wall coordinate, inward direction, start/end, floor Y, length), not just its length, so furniture can be placed without a second query.
