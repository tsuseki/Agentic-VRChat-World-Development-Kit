---
title: A plan-space containment test is only valid within one storey
topic: placement-layout-design
tags: [bulk-delete, multi-level, containment, footprint, git]
summary: Any bulk delete keyed on plan-view geometry in a multi-level world must classify objects by level first, or it deletes legitimate upper-floor props.
---
**Symptom:** A cleanup rule "renderer bounds outside the ground-floor slab footprint -> delete" removed the real offenders (plants generated inside a building) **and** an equal number of legitimate balcony plants on the floor above (y ~ 5.5), which sit outside the ground slab in plan but are perfectly placed in 3D.

**Cause:** A plan-space (XZ) containment test ignores height, so anything on another storey that overhangs the tested footprint looks "outside".

**Fix / rule:**
- Classify each instance by base height first (ground level vs balcony/upper deck), then test it against **that level's** footprint.
- Run any bulk delete with the scene committed to git so an over-delete is a free `git checkout` + reload.

**Verify:** After the sweep, count survivors per level and compare against the expected per-level totals; eyeball the upper levels specifically.
