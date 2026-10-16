---
title: Attributing pixels to a submesh by ray must use the nearest hit across all geometry
topic: agent-workflow-verification
tags: [raycast, pixel mask, moller-trumbore, submesh, measurement]
summary: Testing only 'does this ray hit submesh S' counts every pixel with S somewhere behind it, producing plausible but fake asymmetries; keep the front-most hit and render the mask before quoting numbers.
---
**Symptom:** A pixel-attribution measurement reports a strong one-sided effect (e.g. a 17× port/starboard split on a deck) that a render shows does not exist.
**Cause:** Ray–triangle tests (Möller–Trumbore, used because props have no colliders) asked "does the ray hit submesh S at all", including pixels where S is behind the visible surface. Occluder density differs by side, so contamination is asymmetric and looks like a real bug.
**Fix / rule:** Collect all hits across every submesh of every candidate renderer, sort by `t`, keep the front-most, then compare its submesh index to the target.
**Verify:** Render the pixel set as a coloured overlay and look at it before quoting any number — a mask you have not seen is a hypothesis.
