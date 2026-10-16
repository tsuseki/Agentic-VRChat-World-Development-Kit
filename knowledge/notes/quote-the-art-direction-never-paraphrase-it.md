---
title: Quote the art direction in a reviewer brief, never invent or paraphrase it
topic: agent-workflow-verification
tags: [review, art-direction, brief, design-doc, reference-images]
summary: A reviewer treats your brief as ground truth, so an art direction you inferred rather than quoted from the design doc gets confident work graded against the wrong target for several rounds.
---
**Symptom:** Three consecutive review rounds approved planting graded against a palette ("dry native scrub") that the agent had invented, while the written brief asked for a lush tropical garden. It only surfaced when a later round said "reads as dry scrub, not tropical", and the design doc was re-checked.

**Cause:** The art-direction field of the reviewer brief was paraphrased from memory. A reviewer agent has no conversation history and cannot catch this - you are the only check.

**Fix / rule:**
- The theme / art-direction field of a review brief MUST be quoted from the project's own design document (e.g. `DESIGN.md` / `AGENTS.md`). Re-read the line before each brief.
- If no written brief exists, say so and ask - don't supply a plausible one.
- Give the reviewer the actual reference image file path, not a written colour summary of it; don't invent requirements for parts the reference doesn't show.
- Recoverable mid-run: message the running reviewer with the correction and ask it to judge against the corrected brief and call out the difference as a finding.
