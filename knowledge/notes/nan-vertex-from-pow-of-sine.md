---
title: Pow of a sine at its zero produces NaN vertices and nameless 'Invalid AABB' asserts
topic: geometry-meshes-uvs
tags: [procedural mesh, NaN, Mathf.Pow, bounds, Invalid AABB]
summary: Mathf.Sin(π) is slightly negative, Pow(negative, fractional) is NaN, and one NaN vertex poisons the mesh bounds; clamp to zero first and sweep generated meshes for NaN bounds.
---
**Symptom:** Console floods with `Invalid worldAABB. Object is too large or too far away from the origin.` / `Invalid AABB a`, naming no object; the scene still saves.
**Cause:** A lathe profile `r = 0.5f * Mathf.Pow(Mathf.Sin(th), 0.78f)` at `th = π` gets `Sin ≈ -8.7e-8`; `Pow` of a negative to a fractional power is NaN. `RecalculateBounds` → `(Infinity, NaN, Infinity)`.
**Fix / rule:** `Mathf.Pow(Mathf.Max(0f, Mathf.Sin(th)), k)`. Same for any `Pow`, `Sqrt` or `Log` of a trig term touching zero.
**Verify:** After generating meshes, sweep every MeshRenderer/MeshFilter for `float.IsNaN`/`IsInfinity` on `bounds.center` and `bounds.size`; assert count 0. Names the offender in one call.
