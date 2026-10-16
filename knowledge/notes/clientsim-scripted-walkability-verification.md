---
title: Verify walkability by script: ClientSim setup, step limit and a capsule-march sweep
topic: colliders-physics
tags: [clientsim, walkability, stairs, OverlapCapsule, teleport, verification]
summary: Validate routes without hand-play by marching a player capsule along them in edit mode, then a ClientSim teleport tour; ensure the active scene holds the scene descriptor.
---
**When:** Proving a greybox or level is walkable without playing it by hand.
**How:**
- **Capsule march (edit mode):** sample route polylines every 0.1–0.25 m; per sample (1) raycast down from lastGround+1.5 for ground, (2) flag rises > 0.31 m, (3) `Physics.OverlapCapsule(ground+0.6, ground+1.45, r=0.24)` for blockers. Catches gaps, low lintels and over-tall steps. Call `Physics.SyncTransforms()` first if colliders moved in the same call.
- **Step limit:** ClientSim's CharacterController steps ~0.3 m; 0.4–0.5 m steps force jumping. Build ~0.25 m rises (or a smooth ramp collider; a 26.6° rotated box ramp worked under the default 45° slope limit).
- **ClientSim tour:** `LocalPlayer.TeleportTo`, then read position and `IsPlayerGrounded()` in the NEXT call (same-call reads are same-frame) to catch fall-through.
**Pitfalls:**
- ClientSim silently refuses to start if the ACTIVE scene lacks a VRC scene descriptor ("Cannot start ClientSim if there is no scene descriptor!", `LocalPlayer` null) — e.g. an additive test scene became active. `SetActiveScene(main)` or close the extra scene first.
- One-shot `AudioSource.Play()` can start and finish between two tool calls (reads as never played). Temporarily set `loop = true` in play mode before triggering, check `isPlaying`, then restore.
