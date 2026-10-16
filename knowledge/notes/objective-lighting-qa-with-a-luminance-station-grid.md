---
title: Grade lighting objectively: eye-height station grid, mean / dark% / blown%
topic: agent-workflow-verification
tags: [lighting QA, luminance, metrics, RenderTexture, before-after]
summary: Render eye-height views at a grid of stations and four yaws, and report mean luminance, dark% (L<0.05) and blown% (L>0.9) for before/after comparisons.
---
**How:**
- Grid of stations over the floor: raycast down for floor Y, camera at + the WORLD.md reference eye height (default 1.2 m), 4 yaws each, rendered to a persistent capture camera RenderTexture.
- Per station compute **mean luminance, dark % (L < 0.05), blown % (L > 0.9)** — catches both failure directions in one number set. A dark-interior hall target that read well: mean ~0.165, dark ~4 %, blown < 1 %.
- Keep one **fixed-pose** shot for exact A/B across bakes; compare in linear (`mean^2.2`).
- Measure region luminance before proposing a fix (e.g. ceiling vs floor vs windows vs furniture).

**Pitfalls:**
- Stations reading 12–20 % dark can be false positives: cameras inside dark-albedo geometry (cage rows). Screenshot the worst station before "fixing" it.
- Reported texture-scale mismatches need measuring: per-submesh texel density `sqrt(ΣUV area / Σworld area) × mainTextureScale` was a uniform 4.00 m/repeat everywhere in one case — perceived differences came from lightmap resolution or viewing angle.
- `GameObject.Find` misses a capture camera once it is inactive; walk `scene.GetRootGameObjects()`.
