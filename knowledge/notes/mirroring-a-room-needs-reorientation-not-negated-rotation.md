---
title: Mirroring a room layout: re-orient handed props from geometry
topic: placement-layout-design
tags: [mirror, reflection, rotation, orientation, furniture, back axis, layout]
summary: Reflecting a room by negating rotationY flips asymmetric props backwards because a reflection is not a rotation; solve each prop's orientation from its measured back axis.
---
**Symptom:** A mirrored copy of a bedroom (`x' = 2c - x`, `rotY' = -rotY`) has its bed's headboard facing into the middle of the room.

**Cause:** That formula is correct for a *direction*, wrong for an asymmetric *mesh*. A reflection has determinant -1 and no rotation reproduces it. (Negative scale would, but it inverts normals and Unity flags negative `lossyScale`.)

**Fix / rule:** Solve orientation from geometry. A prefab's **back axis** is the XZ centroid of the tallest 25% of its vertices relative to the footprint centroid; that finds a headboard, backrest or a shelf's solid side without knowing the prefab. Aim it (into the wall for casework, away from the served object for seating):

```
ry = atan2(want.x, want.z) - atan2(back.x, back.z)
// Unity Ry: x' = x cos + z sin ; z' = -x sin + z cos
```

Re-seat after rotating: keep the XZ bounds centre and drop `min.y` to the floor.

**Pitfalls:**
- An **L-sectional**'s tall centroid lies on the bisector of its two backs, so the solver returns 45° off; set sectionals square by hand. **Low curved seats** (chaise, stool) report no back axis; leave them.
- The same probe audits existing work: chairs whose back was local +X had been placed by eye facing the window instead of the coffee table. If a seat angle was set by eye, measure it.

Related: [prefab-front-axis-varies-within-a-pack](prefab-front-axis-varies-within-a-pack.md), [vertex-density-cannot-tell-which-way-furniture-faces](vertex-density-cannot-tell-which-way-furniture-faces.md)
