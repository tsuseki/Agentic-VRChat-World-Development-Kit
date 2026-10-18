---
title: A multi-ring root flare on a thick lobed trunk bulges into a plinth; use one step scaled to the trunk
topic: blender-modeling
tags: [trees, trunk, root flare, bark mesh, cross-section, lobes]
summary: Multi-ring flares copied a lobed trunk's cross-section wobble and bulged (a ring 0.3 m up wider than the ground ring), reading as a stone plinth; a one-step flare (1.25× over 0.8 m) reads as a clean taper; scale flare height with trunk radius.
---
**Symptom:** The base of a thick, lobed trunk read as a stone plinth: a ring 0.3 m above the ground was wider than the ground ring.

**Cause:** The flare widened each of several rings by an eased factor, but each ring also carried the trunk's lobed cross-section wobble; on a big radius the wobble plus the flare overshot the ground ring, making a bulge instead of a taper.

**Fix / rule:** On big trunks use a one-step flare: 1.25× radius at the ground easing back over 0.8 m, with flare height scaled to the trunk radius (short flares only on slim stems). The ground ring must be the widest.

**Verify:** per stem, ring radii (max over the cross-section) must decrease monotonically from z = 0 up the flare; side render at eye height of the trunk base.
