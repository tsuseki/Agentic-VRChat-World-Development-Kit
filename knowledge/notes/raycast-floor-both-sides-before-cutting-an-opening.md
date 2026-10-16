---
title: Raycast for floor on both sides of a wall before cutting a door into it
topic: placement-layout-design
tags: [door, opening, void, raycast, collider, curtain wall]
summary: A bay that looks symmetric on the elevation can open onto a double-height void; scan for floor on both sides before choosing where to cut a door.
---
**Symptom:** You need to add doors "one each side of the stairway". The obvious bays (the glass panels flanking the stair centreline) are visually symmetric and ordinary full-height panels, but on the interior side they open onto a ~5 m drop into the double-height void the stair descends through.

**Cause:** The elevation hides what lies behind the wall line. Physics colliders hide it too: the void guard is usually a thin fin collider, which an `OverlapBox` on the doorway reports as "one blocker", indistinguishable from a mullion.

**Fix / rule:** Before choosing a bay, raycast down from just above floor level at `z = wall + 0.6` and `z = wall - 0.6`, stepping across the whole wall in 0.5 m increments, and print the hit height. A run of misses is a hole. That one scan gives the walkable band on each side and the real door candidates, for less than the cost of the render that would have caught it.

Cutting the renderer is only half the job: the wall's collider is usually **one long box**. Split it into segments around each opening and add a head segment above the door, or the new door is a solid invisible wall.

**Verify:** The floor scan shows a hit on both sides across the full door width, and a player capsule passes through the opening.
