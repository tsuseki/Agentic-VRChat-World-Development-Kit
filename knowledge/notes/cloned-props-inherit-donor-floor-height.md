---
title: A cloned prop keeps its donor floor height — re-seat it on the destination floor
topic: placement-layout-design
tags: [duplicate, clone, floor height, bounds, burial, placement]
summary: Duplicating a prop across a floor-level boundary copies the donor Y, so every clone arrives buried (or floating) by exactly the step height.
---
**Symptom:** Planters cloned from the ground (y = 0) onto a deck (top y = 0.060) all show no visible base. Hierarchy and relative-offset checks look perfect because the parts are correct relative to each other.

**Cause:** Placement copied the donor's Y. Worlds often have several floor levels a few centimetres apart (ground 0, deck pads 0.060, podium 0.60) — exactly the range where a burial is invisible in a plan-view screenshot and obvious at eye level.

**Fix / rule:** placement is `donorY + (destFloor - donorFloor)`; never copy Y. After moving, assert against the destination using the **lowest** renderer of the group, and lift the **group root** so siblings keep their relationship:
```csharp
float deckTop = 0.060f;
float dy = deckTop - r.bounds.min.y;
if (Mathf.Abs(dy) > 0.001f) { clone.transform.position += new Vector3(0, dy, 0); }
```

**Verify:** render at standing eye height; check `bounds.min.y` of every clone against the destination floor.
