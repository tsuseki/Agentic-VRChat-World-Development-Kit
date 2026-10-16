---
title: Check how a prop is meant to mount before seating it on the floor
topic: placement-layout-design
tags: [placement, prop seating, speakers, mounting, render check]
summary: Lowest-vertex-to-floor seating never fails, so ceiling- or rig-mounted props end up balanced on a corner; check the source folder and render once from a low oblique angle.
---
**Symptom:** A "speaker" placed on the floor reads as a fallen-over pile or as lying on its back.
**Cause:** `t.position += new Vector3(0, floorY - bounds.min.y, 0)` cannot fail and reports nothing. One prop was a flown line-array cluster meant to hang from rigging (on the floor: balanced on a rear corner, 12.5 cm gap under two thirds of the base); another was a stage-monitor wedge. A pitch sweep scoring "vertices touching the floor" confidently answered the wrong question.
**Fix / rule:**
- Before seating an unfamiliar pack prop, look at its source folder (`stage items`, `ceiling`, `wall`) and render it once from a low oblique angle.
- If the base contact patch is a small fraction of the footprint, it's a mounting mismatch — mount it as authored or pick another prop; don't tune rotation.
- Generic names ("speaker", "lamp", "light") say nothing about how a prop attaches.
