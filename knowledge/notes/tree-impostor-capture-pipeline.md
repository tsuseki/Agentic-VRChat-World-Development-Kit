---
title: Bake distant terrain vegetation into cross-billboard impostors captured in-editor
topic: performance
tags: [impostors, billboards, terrain trees, LODGroup, difference matting, vegetation, triangles]
summary: Capture the real tree prefabs to billboard sheets with black/white difference matting and swap terrain prototypes to 6-tri cross meshes; tens of millions of vegetation tris dropped below 100k with an identical look at long range.
---
**When:** Vegetation is only ever seen from ≥140-200 m (e.g. from altitude). A 6-tri billboard textured with a render of the *real* tree is visually identical to a 2.6-6.3k-tri mesh, and inherits the scene's exact colour grading by construction, unlike a downloaded low-poly pack. Result in one world: ~30M+ visible vegetation tris -> < 100k. Keep the originals in the project as revert path and capture source.

**How (capture via editor script):**
1. Instantiate the original prefab at an isolated spot; `LODGroup.ForceLOD(0)`; set its renderers' light/reflection-probe usage Off. If the in-scene vegetation renders emission-only, set ambient trilight (sky/equator/ground) black inside try/finally so captures match (validate with an A/B brightness check).
2. Orthographic camera, square aspect, `orthographicSize = S = max bounds extent`, camera at S+2 outside bounds. Views: side0 (-Z), side90 (-X), top (+Y, up = +Z).
3. Render each view twice (black and white background) and difference-matte in **linear** space: `a = 1 - mean(lin(white) - lin(black))`, `rgb = lin(black)/a -> gamma`. Pack 1024² tiles into one 2048² RGBA sheet: side0 (0,0), side90 (1024,0), top (0,1024).
4. Import with mipmaps on + **Mip Maps Preserve Coverage, alphaTestReferenceValue 0.4** (otherwise crowns thin at distance), Clamp, max size 1024 (512 for bushes/grass).
5. Mesh in prefab-local space keyed to captured bounds (centre c, half-size S): a vertical XY quad at z = c.z (side0 tile), a vertical ZY quad at x = c.x (side90 tile), a horizontal cap quad at y = minY + 0.5·height (0.62 for broadleaf) (top tile). 6 tris; bushes 2 quads. Mirrored textures are fine (trees are not chiral).
6. Material: unlit passthrough + cutout 0.4 + its own fog matching scene fog + `multi_compile_instancing` + VR stereo macros, `Cull Off`, `enableInstancing = true`.
7. Prefab: root MeshFilter + MeshRenderer (shadows off, probes off) + **LODGroup (single LOD, cull 0.002, fadeMode None)**. Required for terrain trees: tree prototypes without a LODGroup ignore painted `TreeInstance` rotations (and only those trigger the "must use Nature/Soft Occlusion shader" warnings). Grass detail prototypes: no LODGroup, single-GameObject root.
8. Swap in the TerrainData asset (no scene save needed): `td.treePrototypes[i].prefab = imp; td.treePrototypes = arr; td.RefreshPrototypes(); td.SetTreeInstances(td.treeInstances, true); terrain.Flush(); EditorUtility.SetDirty(td); AssetDatabase.SaveAssets();`. Grass: same via `td.detailPrototypes[i].prototype`.

**Pitfalls:** `UnityStats.triangles` reads 0 after a manual `cam.Render()` to a RenderTexture (game view only); compute before/after tris arithmetically. Tree instance width/height scales multiply the prototype's natural size, so meshes built at captured world bounds keep painted sizes 1:1.

Related: [terrain-trees-refresh-popping-and-night-emission](terrain-trees-refresh-popping-and-night-emission.md), [vrchat-camera-clip-planes-and-far-cut-fog-math](vrchat-camera-clip-planes-and-far-cut-fog-math.md)
