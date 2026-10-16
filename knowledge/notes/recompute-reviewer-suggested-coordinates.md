---
title: Treat a reviewer's suggested coordinate as a diagnosis — recompute it against the whole assembly
topic: agent-workflow-verification
tags: [review, scene reviewer, bounds, wall art, constraints]
summary: A visual reviewer derives numbers from the part it can see (canvas, not frame), so applying them verbatim can recreate the defect on the next piece; recheck against every part's bounds and report deviations.
---
**Symptom:** A reviewer resolves two conflicting findings with "put canvas 0 at 7.25 and canvas 1 at 7.07; that leaves 0.79 m of wall above the sideboard". Applying it would make the frame rest on the furniture — another open finding.

**Cause:** The number is right for the **canvas** (1.278 m tall → bottom 23 mm above the sideboard) and wrong for the **assembly** (frame 1.398 m tall → bottom 38 mm *behind* the sideboard top). A reviewer sees a render, not the bounds.

**Fix / rule:** before applying any suggested number, recompute it against `Renderer.bounds` of *every* part (frame and canvas, planter and foliage, bezel and lens) and whatever stands beneath. If it doesn't survive, solve the constraint properly (here: one datum for all pieces, one canvas shrunk 8% so its frame cleared the trim) and say in the next review brief that you deviated and why.

**Pitfalls:** the asymmetry also runs the other way — the reviewer's *diagnosis* is usually right even when its arithmetic isn't. Don't dismiss a finding because your own metric disagrees (see [phash-cannot-detect-aspect-distortion](phash-cannot-detect-aspect-distortion.md)).
