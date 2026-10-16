---
title: Shelf board pitch is a hard ceiling on decor height
topic: placement-layout-design
tags: [shelves, decor, clearance, intersection, stacked structures]
summary: Seating decor on a shelf board says nothing about whether it fits under the next board; sweep every dressed object against the board above it.
---
**Symptom:** A 0.50 m ceramic placed on shelving with a 0.48 m board pitch intersects the board above on every shelf but the top one. Nothing errors, the object measures correctly seated (`min.y` exactly on the board), and the first render looks fine because the camera is below it.

**Cause:** Placement correctness is not clearance correctness.

**Fix / rule:** After any shelf-dressing pass, measure the board heights per column (upward-facing triangles, as in the size-shelf-props note; real bays vary 0.17–0.39 m within one case, so a single uniform pitch is wrong), resolve each object's board as the highest measured board at or below its `min.y`, skip the top board (open above), and flag anything reaching the next board:

```csharp
float board = boards.Where(y => y <= b.min.y + 0.01f).Max();
float next  = boards.Where(y => y > board + 0.01f).DefaultIfEmpty(float.PositiveInfinity).Min();
if (b.max.y > next - thickness - 0.02f) FLAG;   // next = +inf on the top board
```

Never assume a uniform pitch (`Mathf.Round((min.y - y0) / pitch)` misassigns boards on mixed-bay shelving). The same check applies to nightstands under wall art, counters under upper cabinets, and any decor in a stacked structure.

Related: [size-shelf-props-to-measured-bay](size-shelf-props-to-measured-bay.md), [verify-clearance-by-bounds-not-positions](verify-clearance-by-bounds-not-positions.md)
