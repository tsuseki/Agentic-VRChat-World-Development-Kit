---
title: Bake Light Volumes alone in a scratch copy so the world's lightmaps stay byte-identical
topic: probes-reflection-and-light
tags: [VRC Light Volumes, Bakery, volume-only bake, scratch scene, BakerySkyLight]
summary: To add or re-bake Light Volumes without touching a scene's lightmaps, bake them in a scene copy with every renderer at Scale In Lightmap 0 plus a Bakery sun and sky light, then move the volumes and their atlas into the world.
---
**When:** a world's lightmaps are final (or shared with another scene), but its Light Volumes need a bake.

**How:**
1. `AssetDatabase.CopyAsset` the scene and open the copy; `Lightmapping.lightingDataAsset = null`.
2. Set `m_ScaleInLightmap = 0` on every MeshRenderer and Terrain through `SerializedObject` (0.3 s for 14,588
   renderers): they still occlude and bounce but get no chart.
3. Point the copy's `ftLightmapsStorage.renderSettingsOutPath` at a scratch folder.
4. Add a `BakeryDirectLight` matching the Unity sun (colour, intensity) **and** a `BakerySkyLight` (cubemap from the
   sky/probe `.exr`, 32 samples). With only the Unity Baked sun the volumes came out near black (L0 max 0.068, mean ≈ 0);
   with both: L0 max 1.62, mean 0.71. Both were added at once, so add both.
5. `LoadRenderSettings`, then `RenderButton(false)` (a full Render); check the log for the tracer and GPU name.
6. Open the world additively, `DestroyImmediate` its old volume and manager roots, `MoveGameObjectToScene` the baked
   ones, move the `Lightmaps` folder and the manager atlas (`<scene>/VRCLightVolumes/LightVolumeAtlas.asset`) into the
   world folder.
7. Save the world, close the copy unsaved, delete the scratch folder with the Unity MCP `manage_asset` tool.

**Scripted volume setup (LV 3.0.1):** `EditorApplication.ExecuteMenuItem("GameObject/Light Volume")` creates the volume,
the manager and the hidden Bakery helper in one call; then `LightVolumeTools.RecalculateAdaptiveResolution(volume)` and
`LightVolumeTools.ApplyRuntimeState(volume, true)`, plus the internal
`VRCLightVolumes.LightVolumeManagerEditorBackend.CopyProxyToUdon(proxy)` by reflection from the
`red.sim.LightVolumesEditor` assembly. One outdoor layout: 26 tiles of 64 m plus margin, `VoxelsPerUnit` 0.5 (1.0 at
the spawn tile), ground min −0.5 to max +4 m, 636 k voxels.

**Pitfalls:** a Render Selected Groups attempt in a scene without its own full bake raises Bakery's modal refusal and
freezes the editor.

**Verify:** md5 of the world's lightmaps identical before and after; the manager atlas path is in the world folder and
every volume's baked textures (`Texture0`–`Texture2`) are non-null.
