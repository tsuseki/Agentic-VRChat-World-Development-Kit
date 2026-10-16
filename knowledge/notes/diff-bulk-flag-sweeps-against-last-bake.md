---
title: Diff bulk lighting-flag sweeps against what the last bake actually produced
topic: lighting-baking
tags: [static flags, receiveGI, lightmapIndex, bulk sweep, regression, uv2 gutter]
summary: A scene-wide sweep driven by a UV2-gutter predicate silently reverted 28 just-fixed renderers; snapshot per-renderer lightmapIndex before sweeping and compare expected vs actual touch counts.
---
**Symptom:** A sweep meant to catch ~269 objects (re-unwrap, or drop to probes when UV2 gutters < padding+1 texels) touched 934, including all 28 renderers from a just-shipped review fix. Its own metric reported success.
**Cause:** A sweep predicate written from one diagnosis generalises in unintended ways, and reverted objects satisfy it perfectly. No error appears until a later review.
**Fix / rule:**
- Before any bulk sweep over lighting/static/GI flags, snapshot each renderer's `lightmapIndex` from the previous bake:
```csharp
bool baked = r.lightmapIndex >= 0 && r.lightmapIndex < 65534;
// receiveGI == LightProbes && baked  ->  about to regress this object
```
- Report the count you expected to touch next to the count actually touched; a large gap is the signal.
- A flag is not evidence: 1,414 renderers were `receiveGI = Lightmaps` but only 425 had a real lightmap index.
- Guard mesh rewrites with `AssetDatabase.Contains(mesh)` so shared imported meshes aren't modified.
- Persist UV margins back to `ProBuilderMesh.unwrapParameters.packMargin`, or regeneration reintroduces the bug.
