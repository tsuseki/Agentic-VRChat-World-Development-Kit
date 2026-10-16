---
title: Scripted props are often flat siblings: move the whole set by one delta
topic: placement-layout-design
tags: [composite props, siblings, hierarchy, move, legs, trim, audit]
summary: Scripted furniture is frequently built as flat sibling objects rather than a parented assembly, so moving the visible piece leaves legs, lanterns, soil caps and trim behind; move the set by a shared delta and verify with a pairing test.
---
**Symptom:** Moving a side table's top (`Table_0.transform.position = newSpot`) leaves a floating slab: its pedestal (`TLeg_0`) and nearby lantern parts (base/glow/cap/post) stay at the old coordinates. Same for pots (`pot` / `soil` / `curb` siblings), stacked towels, and stair nosing strips left floating after rebuilding the treads.

**Cause:** Earlier scripted passes built props as flat siblings under a room node, sometimes in different branches (furniture vs lighting). Overlap audits read *less* overlap after the move and report success; a "floating" check on the top passes because the top is supposed to be off the ground.

**Fix / rule:**
- Before moving any prop, list its companions by name prefix and move the whole set by one shared `delta` (`+= delta`), never by assigning an absolute position to one piece. Skip companions whose parent is also in the set, or they move twice.
- Architecture has the same shape: trim, nosings, curbs, lips, skirts and glow strips are siblings of what they trim. After any scripted geometry move, sweep the **old footprint** for long thin renderers; the debris is where the object *was*.

**Verify:** Use a pairing assertion, not an overlap count: `gap = top.bounds.min.y - leg.bounds.max.y` must be ~0, and the leg's foot must be on the floor. Beware the false negative: a leg left inside a big neighbouring prop (sofa, lounger) reads as "carried"; exclude known large props from the "what rests on this leg" search.

Related: [moving-furniture-orphans-tabletop-dressing](moving-furniture-orphans-tabletop-dressing.md) covers detecting stranded tabletop dressing.
