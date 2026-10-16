---
title: Fix a dark probe-lit prop on a lighting boundary with Renderer.probeAnchor, not extra probes
topic: probes-reflection-and-light
tags: [light probes, probeAnchor, spherical harmonics, GetInterpolatedProbe, no rebake]
summary: A probe-lit object's look is set by the SH evaluated in the view direction; when its bounds centre lands between bright and dark probes, park an anchor where the SH matches a good sibling — no rebake needed.
---
**Symptom:** One of three identical table lamps renders at ~0.6× its siblings although its probe L0 is roughly in family (0.271 vs 0.346 / 0.358).

**Cause:** What you see is `sh.Evaluate(normal of the face toward the camera)`, not L0. Per-axis evaluation via `LightProbes.GetInterpolatedProbe(renderer.bounds.center, renderer, out sh)` showed the visible face at **0.376 (good) vs 0.040 (bad)** — a 9× gap inside a 1.3× L0 gap. The bad lamp's centre sat between a bright pocket and a dark one (a probe shadowed by a panel baked 0.041), so tetrahedral interpolation averaged to near-zero on the visible face.

**Fix / rule:**
- Scan interpolated SH over a grid around the object, **match the profile of the sibling that already looks right** (L0, up, down, view direction), and park an empty there as `Renderer.probeAnchor`. Rendered value went 0.372 → 0.704 vs the good lamp's 0.589. No rebake.
- **Don't add probes near the dark object:** five probes 0.31–0.37 m away sat inside the lamp's own glow, baked 0.85–0.96, and overcorrected to 1.44× brighter and lopsided. Copy the working sibling's probe distances or move the anchor instead.

**Verify:** compare SH in the actual view direction, then the render, against the good sibling.
