---
title: Assigning rotation on an FBX prefab instance wipes its Z-up correction
topic: import-fbx-prefabs
tags: [fbx, z-up, rotation, tilt, scale axis, scripted-placement, blender-export, prefab-root]
summary: Z-up FBX prefabs carry a -90 degree X rotation on their root, so a scripted placement or tilt that assigns rotation outright lays every prop on its side; compose yaw and tilt with the source rotation and scale along the model's local axes.
---
**Symptom:** After a scripted placement pass, props are present, the right size and seated on the surface, but lying on their side. From a low camera a planting bed just reads as "a bit sparse". Caught by a plant measuring 0.42 m tall and 1.25 m deep. Same bug on a tilt pass: `t.rotation = Quaternion.Euler(3.5f, 24f, 1.5f)` on two parasols laid both on their sides, sunk 1.7 m through the deck.

**Cause:** A Z-up FBX (Blender exports, most plant/prop packs) imports with a -90 degree X rotation (e.g. `(270, 0, 0)`) on the model root Transform; its upright pose is itself `Euler(270, yaw, 0)`. Assigning `rotation` replaces the correction instead of adding to it. Unit scale correction lives on the root `localScale` the same way (see [fbx-root-transform-carries-unit-scale-and-rotation](fbx-root-transform-carries-unit-scale-and-rotation.md)).

**Fix / rule:** compose, never assign. Safe pattern for any scripted FBX placement:
```csharp
go.transform.SetParent(parent, false);
go.transform.localScale = src.transform.localScale * s;
go.transform.rotation   = Quaternion.Euler(0, yaw, 0) * src.transform.rotation; // src = prefab asset
// then position by measured renderer bounds
```
Tilt goes in world space on top of the correction:
```csharp
// WRONG - throws away the up-axis correction
t.rotation = Quaternion.Euler(tiltX, yaw, tiltZ);
// RIGHT
t.rotation = Quaternion.Euler(tiltX, 0f, tiltZ) * Quaternion.Euler(270f, yaw, 0f);
```
Scale follows the model's local axes: on the parasol the mast runs along **local Z**, so "furl the canopy" is `localScale = (0.17, 0.17, 1.12)`, not `(0.34, 1.16, 0.34)`.

**Verify:** For anything that should stand upright, assert `bounds.size.y > 0.55 * max(size.x, size.z)` and print the failure count in the pass itself. A few genuinely flat items (rosette plants) is normal; most failing means a wiped rotation. After any rotate/scale pass also assert `bounds.min.y >= floorY - 0.05`; a prop diving below the floor has been laid over.
