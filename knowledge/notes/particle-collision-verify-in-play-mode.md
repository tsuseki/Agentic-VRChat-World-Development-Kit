---
title: Verify particle collision in play mode — edit-mode Simulate skips it
topic: audio-video-ui
tags: [particles, collision, sub-emitters, Simulate, play mode, rain]
summary: ParticleSystem.Simulate in edit mode does not evaluate World collision or collision sub-emitters, so scripted edit-mode checks can't judge collision.
---
**Symptom:** After `ParticleSystem.Simulate(t, withChildren, restart)` in edit mode, particles pass through colliders and sub-emitter counts stay 0, with no errors.
**Fix / rule:**
- Enter play mode, wait a few seconds, `GetParticles()`, and count particles inside a volume they should never reach. Compare against the analytic no-collision expectation (box fraction × time in band × count): matching it ⇒ collision inert; far below ⇒ working. Medium-quality voxel collision leaks ~0.5–1% through curved meshes; that's normal.
- Entering play mode domain-reloads and drops the MCP bridge for one call — retry.
- ClientSim spawns its settings menu at the spawn point, blocking screenshots from spawn-adjacent positions; offset the camera.
