---
title: Seat props on the visible floor mesh, not on the collider proxy
topic: placement-layout-design
tags: [floor, collider proxy, raycast, rug, placement, camber]
summary: When the walkable collider is a separate flat proxy, props seated to it can sit under the visible (possibly cambered) floor mesh while every clearance metric reads perfect.
---
**Symptom:** A rug and a stack of books render as a sliver (7% of a disc) and bake pure black, yet "spread 0.0000 m, tilt 0.000°, 1.05 cm proud" all read perfect.

**Cause:** The floor exists twice: a flat collider proxy (y −0.040) and the visible floor mesh (a cambered deck around y −0.020, sloping ~1.7° across the room). Props were seated to the proxy, ~2 cm under what you see. Every metric was measured against the wrong reference surface, and a flat proxy makes flat-and-level look like success. Two full bakes were spent before a render showed the rug wasn't there.

**Scope:** applies whenever the walkable collider is a separate proxy from the visible floor; downward `Physics.Raycast` seating (for bundle prefabs with junk bounds) is valid only where the collider is the visible surface itself.

**Fix / rule:**
- Get floor height by ray–triangle intersection against the **visible mesh** (its upward-facing triangles) — not `Physics.Raycast` (hits the proxy), not a remembered constant.
- On a cambered surface, fit a least-squares plane over the prop's footprint and align the prop to that normal; a small tilt there is the floor's camber, not a defect.

**Verify:** render it. If an object doesn't appear where expected, do an ON/OFF renderer diff — hiding candidate covering meshes one at a time identifies the occluder in one pass.
