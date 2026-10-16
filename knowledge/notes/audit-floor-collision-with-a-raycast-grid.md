---
title: Audit floor collision with a raycast grid, not spot checks
topic: colliders-physics
tags: [floor, collider, raycast, audit, fall-through, minimal-colliders]
summary: A minimal-collider policy must never reach the floor slab, and a missing floor collider is invisible in the editor, so sweep the walkable area with a downward raycast grid.
---
**Symptom:** Players fall through floors in the spawn room and several others; an upper floor drops straight to the one below. Nothing renders differently, no warning fires, screenshots look perfect. In one world 41% of floor 1 had no collider.

**Cause:** "Colliders only on walls and big solid masses" was applied to the floor slab too. Spot checks lie: a ray in a kitchen "hits" at y = 0.96 because it landed on the island; one upstairs "hits" because it fell a whole storey onto furniture below.

**Fix / rule:** Sweep, don't inspect:
```csharp
for (float x = xMin; x <= xMax; x += 2) for (float z = zMin; z <= zMax; z += 2) {
    if (!Physics.Raycast(new Vector3(x, floorY + 3f, z), Vector3.down, out var h, 6f,
                         ~0, QueryTriggerInteraction.Ignore)) misses++;
    else if (h.point.y > floorY + 0.25f) landedOnAProp++;   // NOT proof of a floor
}
```
- Count `landedOnAProp` separately - folding it into "hit" is what makes spot checks lie.
- Fire horizontal rays outward at y = 1.2 on all four sides to confirm players cannot walk off the plate.
- `Undo.AddComponent<BoxCollider>(slabGO)` auto-fits the mesh bounds in **local** space (immune to parent scale skew). Six boxes took one floor from 228/551 misses to 0/551.
- Remaining misses may be legitimately open (double-height voids, balconies) - verify by re-testing those spots, not by accepting the grid total.

**Pitfall:** `Collider.bounds` reads `(0,0,0)` on inactive objects (physics doesn't maintain world bounds for them). A disabled toggle group of colliders will all report zero size - check `BoxCollider.size` (serialized local field) instead.

Related: [non-uniform-parent-scale-desyncs-colliders](non-uniform-parent-scale-desyncs-colliders.md)
