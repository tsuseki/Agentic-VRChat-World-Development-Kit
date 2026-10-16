---
title: Non-uniform scale in a collider parent chain desyncs physics from the gizmo
topic: colliders-physics
tags: [collider, non-uniform-scale, lossyScale, physx, invisible-wall, boxcollider]
summary: A non-uniform scale anywhere above a rotated collider makes PhysX collide with a different box than the gizmo draws, with no warning; keep collider roots at unit scale and put dimensions in BoxCollider.size.
---
**Symptom:** "Colliders move weirdly when I scale or rotate them." Ramps collide a metre above where the gizmo draws them, floors are missing near stairs, an 11.8 m roof panel collides as a 79 m slab. Boxes with identity rotation behave, which makes only some colliders look cursed.

**Cause:** PhysX cannot represent a skewed (sheared) box. With a non-uniform `localScale` on an ancestor (e.g. a `Colliders` root at `(1, 1, 6.7)`) and a rotated child, Unity decomposes the matrix and collides with something else entirely. No warning.

**Fix / rule:**
- Before debugging any collider placement, print `transform.lossyScale` for the collider **and** its ancestors. If not uniform, fix that first - every other measurement is garbage until then.
- Keep the collider root at position 0 / rotation identity / scale 1; give every collider child `localScale = 1` and put real dimensions in `BoxCollider.size`. Rotation on the child is then safe.
- Rotations in exact 90 degree multiples are exempt (axes just permute, no shear) - don't "fix" those.

**Verify:** Compute both boxes and diff them. Physics: center = `position + rotation * Vector3.Scale(lossyScale, bc.center)`, half-extents = `Vector3.Scale(bc.size, lossyScale) / 2`. Gizmo: the 8 local corners through `localToWorldMatrix`. Disagreement = this bug.
