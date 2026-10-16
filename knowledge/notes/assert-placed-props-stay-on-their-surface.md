---
title: Assert placed props' bounds stay inside the surface they sit on
topic: placement-layout-design
tags: [placement, free space, table, floating, bounds, assert]
summary: Free space computed from the min/max of occupants misplaced a vase 13 cm off a table edge; use a real free-interval scan and assert the finished bounds are inside the surface.
---
**Symptom:** Dressing the empty half of a table, pieces were placed at offsets beyond a 0.47 m run; a vase hung 13 cm off the edge, floating.

**Cause:** Two bugs:
1. **min/max is not a gap.** `freeLeft = occupiedMin - tableMin`, `freeRight = tableMax - occupiedMax` collapses all occupants into one span, hiding interior gaps and mis-sizing the end runs.
2. Offsets were relative to the gap start with **no check** that they stayed inside it.

**Fix / rule:** Use a largest-free-interval scan over sorted occupant spans, and assert every placement against the surface:

```csharp
Physics.SyncTransforms();
var nb = BB(host);   // combined renderer bounds of the placed object
bool onSurface = nb.min.x>=b.min.x-0.005f && nb.max.x<=b.max.x+0.005f
              && nb.min.z>=b.min.z-0.005f && nb.max.z<=b.max.z+0.005f;
```

**Verify:** Log `ON SURFACE = YES/NO` for every placement. A floating prop costs a whole review cycle; the assert costs one line.
