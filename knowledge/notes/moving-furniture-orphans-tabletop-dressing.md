---
title: Moving a table leaves its tabletop props hovering — move each dressing group by one delta
topic: placement-layout-design
tags: [declutter, furniture, dressing, siblings, floating props, bounds]
summary: Tabletop dressing is usually authored as siblings, not children, so moving furniture by name strands vases and books in mid-air; detect them by support surface and move each group as a unit.
---
**Symptom:** After a layout pass slides a table and side tables 1.6 m, five tabletop props hover 1.5 m away over bare rug. Nothing errors; no room-level metric moves.

**Cause:** Props live as siblings under the room (e.g. `ROOM/Vase_T`), not children of the table.

**Detecting:** a naive "is there a renderer below this prop's centre?" sweep produced 397 hits, almost all false (sconces, hanging bulbs, fixture trims, door handles, railing posts…). What works: for each candidate, take the highest renderer whose XZ bounds contain the prop's **centre** and whose `max.y <= base + 0.05`; flag `base - surface > 0.02`. Exclude floor slabs/rugs by size. Props in a bay of a taller renderer (bookshelf, cabinet) are a separate case — confirm by scanning the mesh's horizontal triangles, not AABB.

**Fix / rule:** never re-seat props one by one (destroys the arrangement). One delta per group:
```
grp   = union of the group's bounds
delta = (support.center.x - grp.center.x,  support.max.y - grp.min.y,  support.center.z - grp.center.z)
```
Add it to every member.

**Verify:** assert the group's XZ is inside the support footprint, then run a pairwise overlap test on members — pre-existing overlaps travel along and surface here.
