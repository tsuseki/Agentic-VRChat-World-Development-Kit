---
title: Custom layers 22-31 collide with players; particle-collision proxies can become invisible ceilings
topic: colliders-physics
tags: [layers, collision matrix, PlayerLocal, particle collision, proxy collider, stuck player]
summary: Colliders on VRChat custom layers block players by default, and the project's collision matrix is not shipped to clients; keep particle-only proxies out of player space or use a trigger.
---
**Symptom:** Player can turn and crouch but cannot walk. Short avatars (<= 1.6 m) are unaffected, which masks it.

**Cause:** A box collider added only as a particle-collision target (e.g. for rain) on a custom layer (22-31) still blocks players: new layer rows collide with everything, including `PlayerLocal` (10) and `Player` (9). ParticleSystem world collision uses its own `collidesWith` LayerMask and does not need the physics matrix. Worse, an AABB box proxying a curved shape (a balloon ellipsoid) put its flat bottom face 1.61 m above the deck below, an invisible ceiling across the whole area; the capsule penetrates and the controller cannot depenetrate.

**Fix / rule:**
- Do not fix it by unchecking the layer pair in Project Settings > Physics: project settings are not in the world bundle, and the VRChat client uses its own matrix for layers 22-31. The fix will not survive Build & Test.
- Fix the geometry or use a trigger. When proxying a curved shape for particles, only the face the particles strike matters (rain only hits the top), so pull every other face out of player space.
- Particle world collision is skipped by edit-mode `Simulate()`; verify particle behaviour in play mode.

**Verify:** Overlap-test a player capsule (radius 0.2, heights 1.6/1.8/2.0) at the spawn point and along walk paths against all layers (`~0`). Test several avatar heights; do not reason from `bounds`.
