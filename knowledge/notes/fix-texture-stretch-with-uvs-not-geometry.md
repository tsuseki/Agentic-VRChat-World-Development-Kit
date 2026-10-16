---
title: Fix texture stretch with a UV pass, never by rebuilding geometry
topic: geometry-meshes-uvs
tags: [UV, texture stretch, non-uniform scale, bulk sweep, git revert]
summary: Stretched textures from non-unit localScale are a UV defect; a "rebuild at world scale" sweep filtered by a property also replaced spheres, cylinders and rotated parts with axis-aligned boxes.
---
**Symptom:** Wall lining shows anisotropic grain smear. Panels carry non-unit `localScale` (0.629, 0.722, 0.464…), compressing their UVs by exactly `1/scale`.

**Wrong fix:** "rebuild every non-unit-scale panel at world scale". The filter matched 63 objects, not ~15 panels — spherical stones, a cylindrical bucket and ladle, a glass door at `eul=(0,140,0)` — and replaced them all with axis-aligned boxes and zeroed rotations. Nothing errored.

**Fix / rule:**
- Scale the `uv` array of the existing mesh by the transform scale. Assert mesh `bounds.size` and `eulerAngles` are unchanged before saving.
- Match defect class to fix class: texture stretch → UV pass; wrong shape → geometry pass.
- Print and inspect a structural sweep's match list before it writes, especially when the predicate is a **property** (`scale != 1`) rather than an identity (a name list).
- When damage is scripted and fixes are replayable, `git checkout -- <scene>` is a free undo: revert first, replay second — don't repair 63 objects in place.
