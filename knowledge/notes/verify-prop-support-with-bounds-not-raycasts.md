---
title: In a collider-free world, verify prop seating with renderer bounds, not raycasts
topic: placement-layout-design
tags: [floating props, raycast, colliders, bounds, seating, audit, face-mounted]
summary: When props carry no colliders, a downward raycast cannot tell a seated prop from a floating one; test support renderer-bounds against renderer-bounds, then contact-test face-mounted parts.
---
**Symptom:** A float check of the form "raycast down from the prop and measure the gap" returns `no collider` for most props, or reports large numbers of false floaters: 112 "floating" objects, of which 108 were rocks sitting correctly in a colliderless fire-pit trough and 17 shrubs rooted in a colliderless bed. The ray passed through and hit the deck 0.36 m below. The few props that do hit something report just the ray offset plus surface thickness.

**Cause:** Small props are deliberately collider-free (walked through), and big furniture carries one coarse box, so the ray measures collision geometry, not what the player sees.

**Fix / rule:**
1. **Geometric support:** for each part, find other *renderers* whose XZ footprint overlaps and whose `bounds.max.y` is at or below the part's `bounds.min.y`; take the nearest. Supported = gap roughly within [-0.30, +0.05] m. Or, when the intended support is known (shelf board, counter, slab), assert `abs(prop.bounds.min.y - support.bounds.max.y) < tol`. The support has a renderer even without a collider.
2. **Contact test the leftovers:** face-mounted parts (door beads, trim, handles, standoffs) legitimately have nothing beneath them. Use an axis-agnostic contact check against the host: `max(gapX, gapY, gapZ) <= 0`. That isolated a handle floating 21 mm off its lid from beads correctly bedded 4 mm into their door.
3. Fix only what survives both passes.

**Verify:** The raw raycast list buries the single real defect; the two-pass result should be a handful of genuine items.

Related: [verify-clearance-by-bounds-not-positions](verify-clearance-by-bounds-not-positions.md), [free-spot-search-self-match-and-collider-blindness](free-spot-search-self-match-and-collider-blindness.md), [assert-placed-props-stay-on-their-surface](assert-placed-props-stay-on-their-surface.md)
