---
title: If a measurement doesn't change across a swept parameter, it is measuring the wrong geometry
topic: placement-layout-design
tags: [measurement, sweep, parasol, clearance, filtering, head height]
summary: A height-filtered vertex sweep returned the same answer at every yaw because it caught the parasol's own mast; filter radially from the axis, and widen the search before lowering the bar.
---
**Symptom:** Sweeping a tilted parasol's yaw 0–355° to find the lowest canopy point always returned the same value at the mast's XZ.
**Cause:** Filtering `y > 1.2 m` to exclude the base plate still included the mast, collar and hinge, which sit lower than any canopy vertex. Rotating an object cannot move a point on its own axis.
**Fix / rule:**
```csharp
if (new Vector2(w.x - mast.x, w.z - mast.z).magnitude < 0.35f) continue; // skip mast/collar/knuckle
```
- A constant answer across a swept input is the tell that you are measuring the wrong thing.
- When no value of one parameter meets the constraint (best 1.87 m vs a 1.95 m head-height target), widen the search (joint sweep over position and yaw) rather than relaxing the target — it found 2.12 m clearance over every walkable area with the low rim over a lounger.
