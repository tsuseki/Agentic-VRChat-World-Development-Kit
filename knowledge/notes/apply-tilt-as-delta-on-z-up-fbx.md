---
title: Assigning rotation on a Z-up FBX wipes its stand-up correction — apply tilt as a delta
topic: import-fbx-prefabs
tags: [FBX, Z-up, rotation, Quaternion, scale axis, bounds check]
summary: A Z-up model's upright pose is itself a rotation (Euler(270, yaw, 0)); assigning transform.rotation outright lays it on its side, so compose tilt on top of the correction and scale along the model's local axes.
---
**Symptom:** Adding a slight tilt to two parasols with `t.rotation = Quaternion.Euler(3.5f, 24f, 1.5f)` lays both on their sides, sunk 1.7 m through the deck.

**Cause:** They are Z-up FBXs whose upright pose is `Euler(270, yaw, 0)`. Assignment replaced the correction instead of adding to it.

**Fix / rule:**
```csharp
// WRONG - throws away the up-axis correction
t.rotation = Quaternion.Euler(tiltX, yaw, tiltZ);
// RIGHT - tilt in world space, on top of the correction
t.rotation = Quaternion.Euler(tiltX, 0f, tiltZ) * Quaternion.Euler(270f, yaw, 0f);
```
Same confusion hits scale: on that model the mast runs along **local Z**, so "furl the canopy" is `localScale = (0.17, 0.17, 1.12)`, not `(0.34, 1.16, 0.34)`.

**Verify:** after any rotate/scale pass on props, assert `bounds.min.y >= floorY - 0.05`; a prop diving below the floor has been laid over.
