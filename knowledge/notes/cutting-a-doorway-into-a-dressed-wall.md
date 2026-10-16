---
title: Cutting a doorway into a dressed wall: move the dressing, then split the collider
topic: placement-layout-design
tags: [doorway, wall, opening, dressing, shelving, BoxCollider, ProBuilder]
summary: A new opening in a finished wall lands on shelving, art and sconces; inventory and shift the dressing first, retire what cannot move, rebuild the head, and split the wall's collider.
---
**When:** Adding an opening to a wall that has already been styled. In one case the work was 10% geometry and 90% dressing: two casework runs, 246 shelf props, cornice caps, 16 sconces, skirting and pictures, with every free span under 1.5 m, so both openings landed on furniture.

**How:**
1. **Inventory what touches the wall plane first.** Group by parent and list each run's extent along the wall. Shelf props and caps were *siblings* of the shelving carcass, not children; moving the carcass alone leaves the books floating in the doorway (see [move-composite-props-as-sibling-sets](move-composite-props-as-sibling-sets.md)).
2. **Shift the runs** (here +1.25 m and +1.15 m), moving every sibling prop group by the same delta in the same pass, then re-measure the free span.
3. **Retire what cannot move.** Deleting a picture or sconce is better than a 0.3 m squeeze that reads as a mistake.
4. **Cut the opening, then rebuild the head** as its own ProBuilder cube; do not scale the wall.
5. **Split the wall collider.** A `BoxCollider` spanning the whole run ignores the hole, so the player walks into an invisible wall in the doorway. Replace it with one segment collider per remaining solid stretch.

**Pitfalls:** Check the floor slab on the far side before cutting, and extend it if the new space is meant to be reachable.
