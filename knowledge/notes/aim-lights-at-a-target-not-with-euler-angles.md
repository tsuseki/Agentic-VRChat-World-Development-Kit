---
title: Aim spot/wash lights with LookRotation at a target, not hand-written Euler angles
topic: lighting-baking
tags: [spot light, rotation, LookRotation, orientation, bake]
summary: A hand-typed Euler rotation can point a light 180 degrees away from its target and nothing catches it until a full bake later.
---
**Symptom:** After a bake, the surface a set of wash/spot lights was meant to graze is still unlit. Light count, intensity, position and static flags all check out.

**Cause:** A rotation like `Quaternion.Euler(72, 0, 0)` encodes no intent. The pitch looked right, the missing 180 degree yaw was invisible on inspection (the fixtures being replaced had `rotY = 180` precisely because their target was on their -Z side), so all lights pointed into the room instead of at the panel.

**Fix / rule:** Always aim at a point:
```csharp
t.rotation = Quaternion.LookRotation((target - t.position).normalized, Vector3.up);
```
When placing more than one, assert and print the alignment:
```csharp
Vector3.Dot(t.forward, (target - t.position).normalized) > 0.99f
```

**Verify:** The printed dot product for every light is > 0.99 before you start the bake. Orientation errors bake silently and cost a whole bake cycle to find, so check them before baking.
