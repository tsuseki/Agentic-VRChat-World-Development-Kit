---
title: Size shelf props to the measured gap between boards, not the shelf's AABB
topic: placement-layout-design
tags: [shelves, prop placement, clearance, bounds, dressing]
summary: A 2.74 m bookshelf's real bays were 0.17–0.39 m; find boards from upward-facing triangles per column and size props to the bay.
---
**Symptom:** A 0.95 m vase placed on a tall bookshelf spears nine boards; the item it replaced did the same unnoticed.
**Cause:** The shelf's AABB contains anything under its total height; it says nothing about bay headroom.
**Fix / rule:** Measure bays per column: collect triangles with `|world normal.y| > 0.85` whose centroid lies near the column, dedupe centroid Y (~0.04), sort; gaps between consecutive Ys are the bays. Some columns are open shafts that no AABB test distinguishes. Size the prop to the bay and seat its base on the board below.
**Verify:** Re-run the triangle scan and assert zero boards inside the prop's Y-span within its XZ footprint.
**Pitfall:** Prop-vs-shelf AABB overlap is not a defect — contents are supposed to be inside. Confirm with an untouched sibling (e.g. a book) showing the same overlap before discounting, or a clash solver will push contents into the room.
