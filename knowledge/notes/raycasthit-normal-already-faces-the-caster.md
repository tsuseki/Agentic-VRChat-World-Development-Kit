---
title: RaycastHit.normal already points back toward the ray origin
topic: placement-layout-design
tags: [raycast, normal, wall-art, orientation, scripted-placement]
summary: RaycastHit.normal faces the side the ray came from, so negating it to "face into the room" turns every wall-mounted prop toward the wall.
---
**Symptom:** 21 scripted wall pictures are in the hierarchy, right size and position, and invisible from every player angle.

**Cause:** Placement used `Quaternion.LookRotation(-hit.normal)` on the theory that the normal points out of the wall. `RaycastHit.normal` is the surface normal on the side the ray came from - it already points back at the caster, into the room. Negating it faced every canvas into the wall.

**Pitfalls in the diagnosis:**
- You can't re-probe facing with a ray from the prop: it sits a few mm off (or inside) the wall collider, so a ray from its centre starts inside the collider and returns nothing. A detector built that way reported 19 of 21 backwards panels as fine.
- Don't use a raycast at all for facing: take the room's renderer-bounds centre, point the prop at it (dominant axis of `roomCentre - propPos`), and probe the wall plane separately by casting along that axis from a point known to be in open floor.

**Verify:** Check `transform.forward` against the room centre before suspecting materials, layers or culling. Positive control: an existing hand-placed prop on the same wall family; assert new ones agree in sign.

Related: [unity-quad-primitive-faces-minus-z](unity-quad-primitive-faces-minus-z.md)
