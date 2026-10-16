---
title: ParticleSystem world collision at High quality is catastrophic at scale — use emission-shape holes instead
topic: performance
tags: [ParticleSystem, collision, rain, draw calls, emission shape, particleRaycastBudget]
summary: 130k rain particles with High-quality world collision ran ~7 FPS; the same particles without collision ran ~85 FPS — keep rain off covered areas with a ring-shaped emitter instead.
---
**Symptom:** a rain system makes the world "super laggy": ~7 FPS and ~23,000 particle draw calls.

**Cause:** the Collision module, not particle count. Quality **High** does uncached per-particle raycasts every frame and ignores `particleRaycastBudget`. Measured: 130k live particles with High collision ≈ 7 FPS; collision OFF, same 130k ≈ 85 FPS, ~99 draw calls.

**Fix / rule:**
- Turn world collision off. To keep rain out of a ship/roofed area, use an **emission-shape hole**: Circle shape with `radiusThickness` < 1 (e.g. r 500, thickness 0.92 ⇒ spawns only in a 40–500 m ring). No catch-colliders needed.
- `arcMode` must be **Random**; Loop reads as a rotating curtain.
- Size the ring to what is visible: drops beyond ~250 m were sub-pixel at night, so r 500 → 250, rate 20k → 5k, maxParticles 150k → 40k kept identical areal density in the 40–250 m band (~32k alive, ~65k tris).
- A cheaper alternative used later: a few textured cylinder "rain shells" around the player area.

**Pitfalls:** don't conclude a particle system is fine from edit-mode behaviour; ClientSim may strip EditorOnly-tagged systems in play mode.
