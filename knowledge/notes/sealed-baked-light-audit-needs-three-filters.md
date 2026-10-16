---
title: A sealed-light audit needs to skip directional lights, inactive geometry, and lights on a face
topic: lighting-baking
tags: [sealed light, audit, Bounds.Contains, directional light, inactive, escape pass]
summary: A naive bounds.Contains test for lights sealed inside geometry double-counts; skip directional and inactive objects and require a margin so escaped lights on a face are not re-flagged.
---
**Symptom:** An audit for baked lights sealed inside solid geometry (`bounds.Contains(light.position)` over every box mesh) reports 116 sealed lights, including the `Sun`. The true figure was 58, and an escape pass never converges.

**Fix / rule:** All three filters are required:
1. **Skip `LightType.Directional`.** Its transform is only a rotation carrier. The sun appearing in the list is a canary that the test is unfiltered.
2. **Skip inactive objects.** `FindObjectsOfType<MeshRenderer>(true)` sweeps in a dormant blockout layer that occludes nothing in a bake. Gate on `activeInHierarchy && renderer.enabled`.
3. **A light on a face is escaped, not sealed.** `Bounds.Contains` is inclusive, so lights a previous pass pushed to the boundary read as still inside forever. Require a real margin (> ~20 mm on all six faces).

With filters in place the escape converges in one pass: push spots out along their aim, point lights out through the nearest face, re-measure with the same test until it prints 0. Refuse any escape needing more than ~0.6 m of travel and report it: the fixture itself is misplaced, and silently teleporting it hides the real bug.
