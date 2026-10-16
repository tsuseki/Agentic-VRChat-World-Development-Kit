---
title: LODGroup.size never recomputes after a rescale — props cull at a fraction of the intended distance
topic: import-fbx-prefabs
tags: [LODGroup, culling, import scale, terrain trees, prefab]
summary: LODGroup.size is stored, not derived; correcting a prefab's import scale afterwards leaves it e.g. 1/100 of real size, so every instance culls within a few metres and looks never-placed.
---
**Symptom:** Hundreds of placed props (e.g. terrain rocks) are invisible from normal viewing distance. Mesh, materials, count and placement are all correct.
**Cause:** `LODGroup.size` is written once (component added / *Recalculate Bounds*). After an import-scale fix, size stayed at 1/100 of the real extent (0.0276 for a 2.757 m mesh). With relative height ≈ `size / (distance · 2 · tan(fov/2))` and a last LOD threshold of 0.004, they culled beyond ~4.5 m. A bounds sweep won't find it — mesh bounds are fine.
**Fix / rule:** Detect by ratio across the whole set: `lodGroup.size` ÷ max dimension of the union of child `Renderer.bounds`. Healthy = 1.0000; offenders read 0.0100. Fix with `PrefabUtility.LoadPrefabContents` → `lg.size = rendererBoundsMaxDim` → `SaveAsPrefabAsset` → `UnloadPrefabContents`. For terrain trees, follow with `terrainData.RefreshPrototypes()` + `Terrain.Flush()` on every terrain. Probe-lit terrain trees need no rebake.
**Verify:** Use the LARGEST instance for the A/B shot — instance scales spanned 0.035–3.68, and a sampled 14 cm pebble made a working fix look like a 0.01% change.
