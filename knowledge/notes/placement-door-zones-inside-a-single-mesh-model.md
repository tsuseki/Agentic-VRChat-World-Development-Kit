---
title: Check door zones inside a single-mesh building with ray scans
topic: placement-layout-design
tags: [door zone, imported model, raycast, MeshCollider, furniture, review]
summary: A building imported as one mesh has no door object, so find the opening with horizontal rays through the door plane, scan the door zone with a downward ray grid against temporary MeshColliders, and cast an upward ray from each hit to tell a hanging pendant from floor furniture.
---

**Symptom.** Furniture modelled into a cabin delivered as one FBX (a chaise and a stool) stood 0.86 m inside the door zone. The scripted door-zone check passed, because it iterates door objects and this building had none.

**Cause.** The door, the walls and the built-in furniture are all faces of one mesh. Nothing in the hierarchy marks the opening, and furniture in the same mesh is invisible to object-level overlap checks.

**Fix / rule.**
- Add temporary `MeshCollider`s (`DontSave`) to the model's meshes; `Physics.SyncTransforms()`.
- Find the opening: horizontal rays through the door plane about 1.8 m above the floor, stepping 0.02 m along it; the run of misses is the door.
- Scan the zone (opening ± 0.3 m, 0–1.2 m deep, 0.12–2.0 m above the floor) with a 0.04–0.06 m grid of downward rays; any hit in that height band is an intrusion.
- From each hit cast a ray upward: a short hit means the surface hangs from the ceiling (a pendant, a nit); otherwise it is floor furniture (a blocker).
- Destroy the colliders afterwards.

**Verify.** After the fix the scan reported only a pendant at 1.80 m. Positive control: run it on a copy with a box placed 0.5 m inside the zone.
