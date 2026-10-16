---
title: Poly Haven FBX import scale, Z-up vegetation, and terrain detail coverage mode
topic: import-fbx-prefabs
tags: [Poly Haven, FBX, globalScale, Z-up, terrain details, detailScatterMode, CoverageMode]
summary: Poly Haven FBX props import at 1/100 scale, grass/fern meshes are Z-up with centred pivots, and 2022.3 terrain detail layers in CoverageMode take 0-255 percent coverage, not instance counts.
---
**Symptom:** A Poly Haven boulder "doesn't render" (it is 1.3 cm tall); grass/fern meshes render lying flat and half-buried; painted terrain grass shows nothing at all.

**Cause / Fix:**
- **1/100 scale:** the FBX is authored in cm and the importer applies `fileScale 0.01` with `useFileScale = true`. Set `ModelImporter.globalScale = 100` and reimport; fix units in the importer, not by scaling prefab children or instances.
- **Z-up vegetation with centred pivots:** bake corrected mesh copies (rotate verts/normals/tangents -90 degrees on X, shift so `min.y = 0`, save as `.asset`). Decide which files are Z-up once per source file/family, not per mesh by `bounds.size.z > size.y` — that test also lays wide, low Y-up shrubs on their backs (see [resolve-up-axis-per-source-fbx](resolve-up-axis-per-source-fbx.md)). This works for every render path including terrain details.
- **Terrain detail CoverageMode** (`TerrainData.detailScatterMode`, the 2022.3 default): layer values are **0-255 percent coverage**, not instances per cell. Classic recipes writing 0-5 give ~1 % coverage, i.e. nothing visible. Grassland reads well around 60-150.

**Verify:** `td.ComputeDetailInstanceTransforms(px, pz, layer, 1, out b)`: if it returns instances, the data is fine and the problem is density/size, not rendering. For imported props assert `renderer.bounds` is in metres.
