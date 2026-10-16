---
title: Terrain trees: refreshing edits, LOD popping, and per-texture night emission
topic: performance
tags: [terrain, trees, treeMaximumFullLODCount, LODGroup, RefreshPrototypes, SetTreeInstances, detailObjectDistance, emission]
summary: Terrain tree edits need explicit refresh calls, trees without a billboard LOD vanish when the full-LOD cap is hit, and night emission must be normalized per texture.
---
**Refreshing edits:**
- Tree prototype **material** edits do not show until `td.RefreshPrototypes(); terrain.Flush();`. The instanced cache keeps rendering the old state, which looks exactly like "my change had no effect".
- Prefab **LODGroup** edits are not picked up even then; rewrite the instance array: `td.SetTreeInstances(td.treeInstances, true)`.

**Trees popping in/out:**
- `Terrain.treeMaximumFullLODCount` (default 5000) is a per-terrain cap on full-LOD trees. Prototypes with **no billboard LOD do not fall back; they vanish** when evicted. With 5-14k trees in range this popped trees at 400-600 m. Raise it above the worst-case in-range count (20000 in that scene).
- Bush prototypes with LODGroups (fadeMode None, no billboard) culled at last-LOD screen height 0.01, roughly 380-700 m (scales with painted width and `QualitySettings.lodBias`; measure empirically with a plant/remove pixel diff rather than trusting `LODGroup.size` math). Lowering the last-LOD threshold to 0.002 moved the cull past the tree distance where fog hides it.
- Do not cure popping by raising content distances: extending `treeDistance` and `detailObjectDistance` made the world badly laggy. `detailObjectDistance` 1000 measured ~3x the frame cost of 250-800. The camera far clip plane by itself costs little; content distances are what lag. Mesh details have no fade, so the detail ring stays a hard pop.

**Night trees and emission (in a scene where tree shaders ignored ambient and probes):** material emission may be the only lever on tree brightness; check with an ambient change and a pixel diff before spending time on ambient/probe settings. Emission out = emissionColor x texture, and texture mean luminance varies ~10x between assets, so one shared emission colour fails on brightness **and hue** (a red-leaf bush glows blood-red, yellow grass glows lime). Normalize per material: sample the texture mean via `Blit` -> `ReadPixels` (works on non-readable textures; values are linear), then per channel `emis = targetHue * targetLum / texMeanRGB`, scaling all channels down proportionally if any exceeds 1 (never clamp per channel; that washes hue toward white).

**Verify:** After a regeneration step reports success, check the actual data changed (sample heights/positions); stale console lines can match a completion filter.
