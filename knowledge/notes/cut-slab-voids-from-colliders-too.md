---
title: When a slab is cut for a stair void, cut its collider too — and prove it with a headroom raycast
topic: colliders-physics
tags: [collider, stairwell, ceiling, BoxCollider, headroom, raycast, invisible wall]
summary: Renderers cut around a stair void while one big BoxCollider still spans the slab seals the stairwell invisibly; only a headroom raycast walk finds it.
---
**Symptom:** Every screenshot of a feature stair looks perfect, through several bakes and reviews, but players climbing it hit their head at the ceiling plane and cannot reach the upper floor.

**Cause:** Ceiling renderers were split into four pieces around the 8 × 7 m void; the collider was a single `BoxCollider` spanning the whole slab. Nothing renders a collider.

**Fix / rule:** whenever a slab is cut for a void (stair openings, mezzanine cut-outs, lift shafts, roof hatches), cut its collider the same way. Collision has to be measured, never looked at.

**Verify — headroom walk along the route:**
```csharp
Physics.SyncTransforms();
for (float z = zBottom; z <= zTop; z += 0.5f) {
  var all = Physics.RaycastAll(new Vector3(xCentre, ceilingY + 4f, z), Vector3.down, 12f);
  float walk = all.Where(h => IsWalkable(h.collider)).Max(h => h.point.y);
  float head = all.Where(h => h.point.y > walk + 0.2f).Min(h => h.point.y) - walk;   // 99 = open
  // assert head > 2.2 everywhere on the route
}
```
