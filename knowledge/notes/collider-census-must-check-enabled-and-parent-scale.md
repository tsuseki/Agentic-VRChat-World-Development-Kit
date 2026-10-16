---
title: A collider census must check Collider.enabled and parent scale, not just activeInHierarchy
topic: colliders-physics
tags: [collider, census, enabled, lossyScale, invisible wall, blockout]
summary: Disabled blockout colliders read as live in an activeInHierarchy census, and boxes authored with world coordinates under a scaled parent become invisible walls far away.
---
**Symptom:** a census reports colliders that don't block anything; or players hit invisible walls far from any geometry.

**Cause / rules:**
- Old blockout `Floor/Ceiling/Wall_*` boxes often sit ~10 cm in front of the visible shell face. Disable their colliders (`enabled = false`) rather than deleting if you want them as reference — and **always check `Collider.enabled`** in audits, not only `activeInHierarchy`. Re-enabling them puts an invisible wall inside every room.
- Cluster boxes (e.g. `*_Props`) whose centres were authored as **world** coordinates under a parent with non-unit scale (e.g. 1.4) end up hundreds of metres away. Sweep for collider bounds far outside their parent's renderer bounds.
- Thin flat shell walls can legitimately stay `MeshCollider` (single-face quads, a few hundred tris), unlike detailed props.
- Mesh bars (cages, cell bars) can let a player squeeze through slivers at panel ends; a box from `mesh.bounds`, or 4 thin walls just inside the mesh face plus a roof, closes them. One measured rework: 41,630 → 1,834 collider tris.

See also [non-uniform-parent-scale-desyncs-colliders](non-uniform-parent-scale-desyncs-colliders.md).
