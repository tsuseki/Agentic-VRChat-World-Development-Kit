---
title: Cap a prop's size before clamping it inside its container
topic: placement-layout-design
tags: [scatter, clamp, bounds, planter, overhang, scale]
summary: A push-inside clamp silently fails when the prop is wider than its container; scale the prop to fit first, then clamp position.
---
**Symptom:** Shrubs scattered into planting beds with a standard clamp still overhung the walkway (20 of 132, by up to 0.84 m). Every "did the position move inside?" check passed.

```csharp
float ox = Mathf.Max(bed.min.x - b.min.x, 0f) + Mathf.Min(bed.max.x - b.max.x, 0f);
obj.position += new Vector3(ox, ..., oz);
```

**Cause:** Beds were 1.0 m wide; randomised shrub width ran to 1.17 m. When the prop is wider than the container both terms fire and cancel, so it straddles and pokes out on both sides. The clamp did exactly what it was told and reported no error.

**Fix / rule:** fix the size first, then the position:

```csharp
float need = Mathf.Min((bed.size.x - margin) / b.size.x, (bed.size.z - margin) / b.size.z);
if (need < 1f) obj.localScale *= Mathf.Max(need, 0.35f);   // cannot be wider than its bed
Physics.SyncTransforms();                                   // re-measure before clamping
// ...then clamp position
```

Iterate two or three passes: rescaling changes the bounds, and a rotated prop's AABB changes again after the move.

**Verify:** An overhang audit that reports a *cluster* of same-magnitude failures, only in the narrowest containers, is a fit problem, not a placement problem.
