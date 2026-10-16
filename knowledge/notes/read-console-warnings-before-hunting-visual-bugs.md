---
title: Read Unity Console warnings before building any detector for a visual bug
topic: agent-workflow-verification
tags: [console, warnings, light probes, malformed tetrahedron, debugging]
summary: Unity often names the exact defect — and its world position — in a repeated warning nobody reads; check errors and warnings before forming a hypothesis.
---
**Symptom:** A blinking bush; hours of instrumented hunts (per-frame colour scans, full-mip texture sweeps, water/probe A/B tests) all come back clean.

**Cause:** The Console was printing `Light Probe tetrahedron is malformed ... at (x, y, z)` 999+ times, with the coordinates of the problem (an object outside the probe hull).

**Fix / rule:**
- On any "something looks wrong" report, read the Console for **errors and warnings** first (Unity MCP `read_console`). Filter by a symptom keyword, then also read the unfiltered tail — the useful warning rarely contains the word you'd guess.
- Warnings repeated 999+ times are signal. One naming a world position or object points straight at the culprit.
- Also check the Lighting window and the Inspector's warning strips for scene-level issues the Console doesn't show.

**Verify:** prove the fix with a rendered before/after afterwards.
