# Performance lessons

Proven rules for keeping VRChat world frame cost, triangles and VRAM down, beyond the harness and recipes in SKILL.md.
Distilled from the knowledge notes for this topic; grep .omp/knowledge/notes/ for the full evidence.

## Budget and attribute triangles

- **Budget triangles per player viewpoint, not per scene (~3 M visible from any reachable spot as a ceiling)** — the camera's per-frame load is what hurts; check worst-case sightlines (long halls, balconies, views between zones) and enforce with baked occlusion, far clip, LODGroups and walls that keep zones partitioned.
- **Census triangles by source asset (n, total, per-instance) before touching density knobs** — one 3k-tri accent × 604 instances was 56 % of a planting; decimating that one asset beat every count/grid tweak, and multi-submesh foliage floors out under decimation so demote it to rare accents.

## Vegetation and terrain

- **Capture far-only vegetation as 6-tri cross impostors from the real prefabs, then ship them merged into per-cell meshes rather than as terrain-tree prototypes** — black/white difference matting in linear space and Preserve Coverage mips at alpha 0.4 give an identical look at long range with tens of millions of tris gone; as LODGroup terrain trees the same impostors still cost ~9 ms CPU at 34k instances.
- **Merge terrain scatter into per-cell meshes and keep `treeDistance`/`detailObjectDistance` at 0; delete what reads as a few pixels from real player viewpoints** — LODGroup terrain trees and detail grass cost ~9 ms and ~15 ms CPU even when each instance is tiny; see SKILL.md §The structural fix and §Judge visibility.
- **Where terrain trees remain, after edits call `RefreshPrototypes()` + `Flush()` (material) or `SetTreeInstances(..., true)` (LODGroup); never cure popping by raising content distances; normalize night emission per texture** — the instance cache looks like "no effect", longer tree/detail distances lag badly, and one shared emission colour fails on brightness and hue because texture means vary ~10×.

## Geometry swaps and culling

- **Swap heavy repeated props to decimated meshes via `MeshFilter.sharedMesh`, keeping material slot names and order** — per-renderer material overrides survive only if slot order holds; strip old Z-up −90° compensation and recheck import scale (m vs cm sources).
- **Zone-cull by toggling `Renderer.enabled`/`Light.enabled` per area from a local script, never `SetActive` the area root** — disabled objects stop getting network events; cache only renderers enabled at Start, keep the current zone when the player is in no box, and audit zones with `renderer.bounds` in edit mode.

## Lights and particles

- **Keep the sun a Baked light, never realtime or Mixed (shadowmask included), and light everything that moves with VRC Light Volumes (light probes as the fallback)** — realtime cascades over a big world are a top avoidable cost on low-end PCs; aim for big-scale shadows only.
- **Turn off ParticleSystem world collision; keep rain off covered areas with a ring emission shape (`radiusThickness` < 1, `arcMode` Random)** — High-quality collision ignores the raycast budget (7 FPS vs 85 FPS for the same 130k particles); see SKILL.md §Where the cost actually hides. Size the ring to what is visible.

## Textures and VRAM

- **Audit texture slots from the material (`GetTexturePropertyNames`) and clear orphans through `SerializedObject` `m_SavedProperties.m_TexEnvs`** — a texture on a property the shader no longer exposes still loads, and `HasProperty` returns false so guarded cleanups skip exactly those.
- **Never ship glTFast-imported GLBs; convert to FBX + separate textures or delete them** — embedded sub-asset textures bypass the importer (uncompressed RGB24, CPU copies, sometimes no mips); see SKILL.md §Where the cost actually hides.
- **Tag scale references, reference avatars, debug cameras and old particle systems `EditorOnly`** — `SetActive(false)` objects still ship and load their textures; EditorOnly strips the object and children at build time.
- **Count unique models in any Udon pool as permanent VRAM, set submission caps (tris + texture size) before collecting content, and start pool members hidden** — Udon cannot instantiate prefabs, so every pooled object's textures load; clones of one model are nearly free, 20 unique 4K cars ≈ 1.3 GB.
