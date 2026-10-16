---
title: Seat props against the surface actually under them, not a global floor height
topic: placement-layout-design
tags: [seating, floor height, podium, occlusion, raycast, invisible prop]
summary: A single global floor height is wrong wherever podiums, pads, steps or plinths overlay the slab; test each prop against every volume in its footprint, and raycast from the camera when a prop seems missing.
---
**Symptom:** A bench, bucket and ladle placed at the deck-top height rendered as nothing at all.

**Cause:** They were inside a raised platform (y 0..0.60) that overlays the deck in that footprint. An AABB "is it on the deck" test passes because the deck is there, underneath.

**Fix / rule:**
- In any space with pads, podiums, steps or plinths, test each prop against **every** overlay volume in its footprint, not just the slab, and seat it on the highest one.
- A prop that renders invisible is usually occluded, not missing. Raycast from the camera to it first: the hit names the occluder in one call.

Related: [seat-props-on-visible-floor-not-collider-proxy](seat-props-on-visible-floor-not-collider-proxy.md)
