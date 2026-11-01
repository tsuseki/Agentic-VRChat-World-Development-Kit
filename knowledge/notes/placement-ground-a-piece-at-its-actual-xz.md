---
title: Take ground height where the piece actually stands, not at its planned point
topic: placement-layout-design
tags: [placement, terrain, ground height, nudges, buried props]
summary: After a piece is nudged from its planned or CSV point, re-sample the ground under its final footprint; a fire pit grounded from its planned point stood on sand 0.27 m higher and was buried.
---

**Symptom.** A fire pit sat 0.27 m deep in the sand.

**Cause.** Its height was taken from the ground at the planned point in the placement table; a later nudge moved it about 5 m to a spot where the sand was higher. Nobody re-sampled.

**Fix / rule.** Ground every piece from samples under its final footprint (after every nudge, rotation and clearance push), against the visible ground surface. Re-run grounding as the last step of every placement pass.

**Verify.** Base-vertex gap per piece (vertices within 0.03 m of its lowest local y, deduplicated on a 5 cm grid): all within the contact tolerance, no piece below −0.03 m.
