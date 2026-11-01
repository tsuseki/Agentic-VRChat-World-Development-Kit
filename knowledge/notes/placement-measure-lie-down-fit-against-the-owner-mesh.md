---
title: Measure lie-down collider fit with a ray grid against the owner's own meshes
topic: placement-layout-design
tags: [lie-down collider, BoxCollider, beds, sofas, raycast, MeshCollider, review]
summary: A lie-down box fits when the median of (box top − mattress or seat surface) is within ±4 mm, measured by a 5×5 ray grid cast down the box's own up axis against temporary MeshColliders on the owning prefab's meshes; eyeballed boxes sat 7–9 cm off and were blockers.
---

**Symptom.** A review found villa beds whose lie-down boxes sat 0.09 m below the mattress (players sink in) and sofas whose boxes sat 0.07 m above the seat (players float). Both were blockers. The boxes had been sized from a spec with an eyeballed centre (1.12 against a mattress top of 1.226).

**Cause.** Nobody measured the box top against the visible surface. Box colliders of disabled slabs give no help either: `Collider.bounds` of an inactive slab has zero extents, so bounds-based checks read nonsense.

**Fix / rule.**
- Add temporary `MeshCollider`s (`hideFlags = DontSave`) to every `MeshFilter` under the slab's owning prefab instance, leaving out the slab's own children; call `Physics.SyncTransforms()`.
- In the box's frame: top = `center.y + size.y / 2`. Cast a 5×5 grid over 90 % of the footprint along `-t.up`, from 0.4 m above the top, max 0.8 m; record hit distance − 0.4 per ray.
- Take the median per slab (it absorbs a back-rest row); pass = |median| ≤ 4 mm. Destroy the colliders.
- Work from the transform plus `center` / `size`, never from `Collider.bounds`.
- Builders: set the box centre to (surface top − size/2), with the top read from the model's build data, not estimated.

**Verify.** Run it over every slab and print `N slabs, M misfit`; a refit pass went from several misfits to 122 slabs, 0 misfits. Positive control: shift one box 1 cm and confirm it is flagged.
