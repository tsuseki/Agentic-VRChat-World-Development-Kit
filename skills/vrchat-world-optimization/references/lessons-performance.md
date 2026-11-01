# Performance lessons

Proven rules for keeping VRChat world frame cost, triangles and VRAM down, beyond the harness and recipes in SKILL.md.
Distilled from the knowledge notes for this topic; grep .omp/knowledge/notes/ for the full evidence.

## Measuring

- **Time only on a quiet CPU: check for Blender and other heavy processes before every timing block, hold launches for the whole window, and discard runs whose `gpuFrameMs` leaves its floor** — background jobs shifted identical baselines by 1.6 ms; on a quiet machine back-to-back baselines differ ≤ 0.47 ms, so compare only within one session in A/B/A passes.
- **Collect job markers (probe sampling) from all threads and use marker breakdowns for composition only** — a main-thread sample showed nothing for a 12.5 ms/frame worker saving, and ~25 enabled recorders inflated `Camera.Render` 6.4 → 10.5 ms.
- **Measure every upload-size tradeoff with a real scene AssetBundle (ChunkBased, ~1 min), not compression estimates; the SDK `.vrcw` is ~0.85× the raw bundle** — estimates for quantized vertex data missed by several MB.
- **Budget triangles only after the first bake** — before it a Baked sun renders realtime shadow passes (7.88 M tris vs 2.6 M after), and play-mode tris on static batches are combined-mesh counts.
- **Make foliage captures deterministic (wind frozen by property block, LOD fade off, water and particles hidden) and require two 0-px "before" sets before any diff counts** — time-driven wind and cross-fade dither make an unchanged scene differ between captures.

## Budget and attribute triangles

- **Budget triangles per player viewpoint, not per scene (~3 M visible from any reachable spot as a ceiling)** — the camera's per-frame load is what hurts; check worst-case sightlines (long halls, balconies, views between zones) and enforce with baked occlusion, far clip, LODGroups and walls that keep zones partitioned.
- **Census triangles by source asset (n, total, per-instance) before touching density knobs** — one 3k-tri accent × 604 instances was 56 % of a planting; decimating that one asset beat every count/grid tweak, and multi-submesh foliage floors out under decimation so demote it to rare accents.

## Vegetation and terrain

- **Capture far-only vegetation as 6-tri cross impostors from the real prefabs, then ship them merged into per-cell meshes rather than as terrain-tree prototypes** — black/white difference matting in linear space and Preserve Coverage mips at alpha 0.4 give an identical look at long range with tens of millions of tris gone; as LODGroup terrain trees the same impostors still cost ~9 ms CPU at 34k instances.
- **Merge terrain scatter into per-cell meshes and keep `treeDistance`/`detailObjectDistance` at 0; delete what reads as a few pixels from real player viewpoints** — LODGroup terrain trees and detail grass cost ~9 ms and ~15 ms CPU even when each instance is tiny; see SKILL.md §The structural fix and §Judge visibility.
- **Where terrain trees remain, after edits call `RefreshPrototypes()` + `Flush()` (material) or `SetTreeInstances(..., true)` (LODGroup); never cure popping by raising content distances; normalize night emission per texture** — the instance cache looks like "no effect", longer tree/detail distances lag badly, and one shared emission colour fails on brightness and hue because texture means vary ~10×.
- **Replace thousands of single-LOD clump prefabs with cells carrying one LODGroup each, and don't rank them from a renderers-off sweep** — `LOD.ComputeLOD` and per-renderer cull/instancing prep run for every LODGroup every frame, visible or not (37k groups ≈ 1.5 + 2 ms on a fast desktop), and turning renderers off leaves that cost in place.
- **Merge probe-lit clumps as vertex-pulled cells (4-byte ids + point-sampled prototype, clump and SH tables), not baked vertex data** — merged vertices took one bundle 182.5 → 218 MB, vertex pulling 189.1 MB, with geometry, hash tint and per-instance SH exact.
- **Before any clump merge, list what the shader derives per object (origin hash, per-instance probe SH) and carry it in vertex data or a table; precompute hash inputs with the GPU's exact rounding** — one probe per cell missed by a median 45 %, and a 1-ulp difference in `sin(...) * 43758` changes the hash.
- **Set `lightProbeUsage = Off` on every lightmapped renderer (0 ≤ `lightmapIndex` < 65534) after each bake, never on probe-lit ones** — Unity still runs probe sampling for lightmapped BlendProbes renderers on worker threads (10,397 renderers 13.0 → 0.53 ms/frame), and Off was 0 px in every view.
- **Clear `BatchingStatic` on instanced LODGroup tree and plant renderers** — static batching stored combined LOD0 copies in the build (394.8 → 168.2 MB after clearing 5,281 renderers, draws 622 → 340); no rebake, prove with a play-mode diff.
- **Set `Terrain.drawInstanced = true` on every terrain tile** — −1,400 draws at spawn over 9 tiles with identical terrain pixels.
- **Turn reflection probes off on instanced tree groups beyond ~30 m of every walk-zone eye point and keep them on inside it** — different blended probes split instancing batches (1,116 → 787 draws); probes off on every tree brightened the woods 16 %.

## Geometry swaps and culling

- **Swap heavy repeated props to decimated meshes via `MeshFilter.sharedMesh`, keeping material slot names and order** — per-renderer material overrides survive only if slot order holds; strip old Z-up −90° compensation and recheck import scale (m vs cm sources).
- **Zone-cull by toggling `Renderer.enabled`/`Light.enabled` per area from a local script, never `SetActive` the area root** — disabled objects stop getting network events; cache only renderers enabled at Start, keep the current zone when the player is in no box, and audit zones with `renderer.bounds` in edit mode.
- **Bake occlusion for any scene copied from another or built new outdoors, with the scatter flagged `OccludeeStatic`** — a copied outdoor scene had no occlusion data (spawn 3,346 → 1,851 batches, `Camera.Render` 24 → 9 ms after a 30 s bake).

## Lights and particles

- **Keep the sun a Baked light, never realtime or Mixed (shadowmask included), and light everything that moves with VRC Light Volumes (light probes as the fallback)** — realtime cascades over a big world are a top avoidable cost on low-end PCs; aim for big-scale shadows only.
- **Turn off ParticleSystem world collision; keep rain off covered areas with a ring emission shape (`radiusThickness` < 1, `arcMode` Random)** — High-quality collision ignores the raycast budget (7 FPS vs 85 FPS for the same 130k particles); see SKILL.md §Where the cost actually hides. Size the ring to what is visible.

## Textures and VRAM

- **Audit texture slots from the material (`GetTexturePropertyNames`) and clear orphans through `SerializedObject` `m_SavedProperties.m_TexEnvs`** — a texture on a property the shader no longer exposes still loads, and `HasProperty` returns false so guarded cleanups skip exactly those.
- **Never ship glTFast-imported GLBs; convert to FBX + separate textures or delete them** — embedded sub-asset textures bypass the importer (uncompressed RGB24, CPU copies, sometimes no mips); see SKILL.md §Where the cost actually hides.
- **Tag scale references, reference avatars, debug cameras and old particle systems `EditorOnly`** — `SetActive(false)` objects still ship and load their textures; EditorOnly strips the object and children at build time.
- **Count unique models in any Udon pool as permanent VRAM, set submission caps (tris + texture size) before collecting content, and start pool members hidden** — Udon cannot instantiate prefabs, so every pooled object's textures load; clones of one model are nearly free, 20 unique 4K cars ≈ 1.3 GB.
- **Cap and swap textures through world-owned `*_World` copies with a rollback pair (normal/mask 1024, crisp-detail materials and the sky left alone)** — shared pack or source assets are read-only for world work, and the caps took one bundle 286.9 → 218.2 MB raw at ≤ 0.016 % px.
- **Crunch big cutout atlases at quality 95 on world-owned copies when upload size is the limit** — 58 MB of BC7 planting atlases became ~15 MB, and quality barely changes size (q70 → q85 +0.6 MB) while q70 showed edge artefacts.
- **Clear `Mesh.isReadable` on world meshes no runtime script reads** — saved ~25.5 MB over 13 meshes.
