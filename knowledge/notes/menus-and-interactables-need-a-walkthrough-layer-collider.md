---
title: Menus and interactables need a collider — put it on the Walkthrough layer
topic: colliders-physics
tags: [Interact, layer, Walkthrough, UI, laser, VRChat layers]
summary: Deleting a settings panel collider during walk-through cleanup silently kills laser clicks; keep the collider on the Walkthrough layer instead of deleting it or making it a trigger.
---
**Symptom:** after stripping colliders so props are walk-through, a world-space settings panel or button can no longer be clicked with the VRChat laser.

**Cause:** VRChat UI raycasts and `Interact()` need a collider. Deleting it looks like correct cleanup.

**Fix / rule:**
- Keep the collider and put the object on the built-in **`Walkthrough` layer (17)** — verified to pass both `Player` and `PlayerLocal`.
- `Interactive` (8) and `Environment` (11) both **collide** with players; don't use them for walk-through interactables.
- Buttons (sink/reset buttons etc.) can be plain `Interact()` overrides on walk-through colliders rather than blocking ones.
Related: [custom-layers-collide-with-players-by-default](custom-layers-collide-with-players-by-default.md).
