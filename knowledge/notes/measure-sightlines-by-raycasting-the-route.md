---
title: Measure sightlines by raycasting the route from the viewer, and raise viewing areas
topic: placement-layout-design
tags: [sightline, occluder, spawn, grandstand, raycast, layout]
summary: Turn "you should see part of the track from spawn" into a number by raycasting the whole route from eye height, and lift spectator areas so the view is not edge-on.
---
**When:** placing occluders, spawn points or spectator areas along a route (racetrack, river, parade path).

**How:**
- Sample the route centreline densely; from the viewer's eye point (+ the reference eye height, default 1.2 m) raycast to each sample and report the **visible fraction** (one layout tuned to 17 %). Occluder placement becomes a number to tune, not an eyeball judgement.
- At ground level a long straight is seen edge-on and nothing can be watched. Raising the hub/paddock on a shelf (6 m worked) turns it into a grandstand.
- Put interactive panels where they don't block the spawn's only view of the action (e.g. on an end wall, not mid-apron).
- Hide the map edge with an outer belt of rocks/terrain; use a few large infield masses as occluders.
- Make everything in a raised area relative to the area's origin **and** height constant, preview cameras included — absolute coordinates get buried when the shelf height changes.
