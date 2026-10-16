---
title: Derive room extents from percentiles of renderer centres, not the union AABB
topic: placement-layout-design
tags: [room-bounds, bounds, percentile, automation, cameras, multi-level]
summary: A room renderer-union AABB is blown out by a few stray children and overlaps neighbours; use the 10th/90th percentile of its own renderer centres and take the floor height the same way.
---
**Symptom:** Automated per-room cameras and an emptiness audit built from `room.GetComponentsInChildren<MeshRenderer>()` bounds land in the wrong rooms. Two "different" rooms show the same furniture on a contact sheet, or a furnished room comes back bare.

**Cause:** A few stray children (a duct, a portal marker, a light rig parented across a partition) blow out the union until different rooms report near-identical AABBs. Separately, rooms on an upper storey get photographed at ground-floor eye height.

**Fix / rule:**
- Use the 10th/90th percentile of the room's own renderer centres for its extents; outliers drop out.
- Take the floor height from the same kind of percentile of `bounds.min.y`, not a constant.
