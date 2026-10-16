---
title: Shelf board pitch is a hard ceiling on decor height
topic: placement-layout-design
tags: [shelves, decor, clearance, intersection, stacked structures]
summary: Seating decor on a shelf board says nothing about whether it fits under the next board; sweep every dressed object against the board above it.
---
**Symptom:** A 0.50 m ceramic placed on shelving with a 0.48 m board pitch intersects the board above on every shelf but the top one. Nothing errors, the object measures correctly seated (`min.y` exactly on the board), and the first render looks fine because the camera is below it.

**Cause:** Placement correctness is not clearance correctness.

**Fix / rule:** After any shelf-dressing pass, resolve each object's board from its own `min.y`, skip the top board (open above), and flag anything taller than the gap:

```csharp
float board = Mathf.Round((b.min.y - y0) / pitch) * pitch + y0;
if (board < topBoard && b.max.y > board + (pitch - thickness - 0.02f)) FLAG;
```

Derive the pitch from the actual board positions; never assume it. The same check applies to nightstands under wall art, counters under upper cabinets, and any decor in a stacked structure.

Related: [size-shelf-props-to-measured-bay](size-shelf-props-to-measured-bay.md), [verify-clearance-by-bounds-not-positions](verify-clearance-by-bounds-not-positions.md)
