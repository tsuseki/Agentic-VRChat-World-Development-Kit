---
title: Moving a landmark does not move its reflection probe
topic: probes-reflection-and-light
tags: [reflection-probe, relocation, specular, skybox-fallback, glossy]
summary: Reflection probes placed in the scene are not re-derived when a scripted builder moves the object they serve, and the symptom shows up elsewhere as a glossy surface reflecting raw sky.
---
**Symptom:** After relocating several landmarks, a nearby glossy rock renders a bright blue "glazed" top. A reviewer reports it as a material defect. The probes still exist, are still Baked, and nothing errors.

**Cause:** The landmark builders positioned the landmark from a code constant, but per-landmark reflection probes lived in the scene and were not moved - they ended up 0.8-1.9 km away. With no local probe, specular fell back to the world probe / raw skybox.

**Fix / rule:**
- After moving any landmark or area, sweep **every** probe against its site, not just the one you touched (all four were stale; review caught one).
- Re-seat each probe over its site (e.g. `bounds.center + 5 m` up if that is the existing convention) and rebake.
- Before blaming glossiness / a gloss map for a mirror-bright surface, check reflection-probe coverage at that position.
