---
title: Pick an emissive overlay's face by where the viewer is, not by axis sign
topic: lighting-baking
tags: [emissive, BakeryLightMesh, screen, double-sided, normals, console]
summary: A single-sided emissive overlay copied from a double-sided screen has a 50% chance of lighting the wrong side; keep the faces whose world normal points toward the seat or spawn.
---
**Symptom:** A thin emissive overlay built to carry a `BakeryLightMesh` on a console's screens throws its light away from the players (e.g. at the window) after a full bake. Every number looks healthy: the light mesh exists, the bake completed, the body kept its lightmap index, the screens render bright.

**Cause:** Console/monitor/sign meshes are usually **double-sided quads** (a front pair and a back pair of triangles, opposite winding). Selecting the pair by axis sign (`worldNormal.z > 0.5`) is a coin flip, made worse by the very common parent rotation `(0,180,0)`, which inverts local-vs-world facing. Nothing in the data distinguishes a correctly oriented emitter from a backwards one; the defect is only the *absence* of spill on the side that matters.

**Fix / rule:**
- Find the viewer first (seat, spawn point, or the open side by raycast), then keep faces with `dot(faceNormal, viewerPos - screenCentre) > 0`.
- Unmirrored readable text in a render tells you which side is the display face.
- Sanity-check: a raked console's correct normal reads something like `(0, +0.48, -0.88)`, toward a seated head, not axis-aligned. A perfectly axis-aligned normal on angled hardware hints you grabbed the wrong pair.

**Verify:** Render from the viewer's position before baking and look for the expected spill.

Related: [bakery-light-mesh-traps](bakery-light-mesh-traps.md), [face-down-decals-bake-black-slabs](face-down-decals-bake-black-slabs.md)
