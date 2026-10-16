---
title: Automated align/centre sweeps need an eligibility filter, a scene-wide clash test and a contact-sensitive threshold
topic: placement-layout-design
tags: [placement, sweep, clash test, bounds, automation, regression]
summary: A "centre X on its nearest Y" sweep will undo earlier fixes and bury objects in artwork unless targets are filtered by meaning, clashes are tested against every renderer, and exact abutment counts as a hit.
---
**Symptom:** A script that centres every wall sconce on the nearest piece of furniture "fixes" one review finding and silently creates two new defects — a sconce centred on a potted plant (re-creating a finding fixed minutes earlier) and another embedded inside a framed painting. The post-move check reported 0 clashes.

**Cause:** three independent bugs:
1. **No eligibility filter.** Targets were "every child of the casework container", which also held a plant and a screen. "Nearest object in the container" ≠ "the thing this fixture is meant to light".
2. **Clash test scoped to the class you were reasoning about.** Only sconce-vs-casework was tested; the painting is not casework.
3. **`overlap > epsilon` cannot see a touch.** Two objects placed by script against the same plane often meet exactly: `oy = 7.30 - 7.30 = 0.0`, so `if (oy > 0.01f)` reports clean.

**Fix / rule:**
1. Filter targets by the semantic relationship, not container membership.
2. Test each moved object against **every renderer in the room/scene**.
3. Use a small negative threshold when contact matters:
   ```csharp
   if (ox > -0.01f && oy > -0.01f && oz > -0.01f)   // catches overlap AND contact
   ```

**Verify:** After any bulk move, re-check the findings you already closed — a sweep that closes one finding can reopen another. Re-render and re-measure instead of trusting `clashes = 0`.
