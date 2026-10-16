---
title: If a targeted fix leaves the metric byte-identical, you changed the wrong thing
topic: agent-workflow-verification
tags: [metrics, diagnosis, positive control, UI colour, linear colour space, renderer toggle]
summary: An unchanged measurement after a targeted edit is information: find the offender by value, and check that the edit reaches the renderer and that the instrument is aimed at the object.
---
**Symptom:** To remove pure-white UI, you dim the header text and slider handles; the render's peak luma stays **0.945 / 1933 px**. Dim them further — still byte-identical.

**Cause:** The peak came from toggle label texts at (0.920, 0.950, 0.970), whose luma is exactly 0.945. The edited elements were just the ones whose *names* sounded brightest.

**Fix / rule:** stop tuning. An unchanged metric means one of:
- you changed something that never produced the number;
- the change isn't reaching the renderer (stale mesh/material copy);
- a bound map multiplies your edit away (Standard's `_EmissionMap` / `_MetallicGlossMap` override the scalar you set);
- **the instrument isn't pointed at the thing** — a renderer-toggle ownership diff returning **0 px** often just means the camera is mis-framed. Always probe a second object known to be in shot as a positive control; if that also reads 0, the camera is wrong. For a submesh, toggle via a per-submesh `MaterialPropertyBlock` (`SetPropertyBlock(block, index)`).

Then identify the offender **by value**: enumerate candidates, compute the metric each would produce, match it to the measured peak.

**Pitfalls:** in Linear colour space a UI colour of 1.0 lands at 255 sRGB and even 0.86 lands at ~0.94 — verify "not pure white" in the render, not the inspector.
