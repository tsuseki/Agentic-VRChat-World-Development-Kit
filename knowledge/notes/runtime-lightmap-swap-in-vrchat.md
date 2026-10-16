---
title: Two baked lighting states can be swapped at runtime in VRChat via Renderer.lightmapIndex
topic: lighting-baking
tags: [lightmap swap, day/night, Udon, lightmapIndex, Bakery, ftLightmapsStorage, BC6H]
summary: Renderer.lightmapIndex and lightmapScaleOffset setters are Udon-exposed and Bakery rebinds lightmaps at runtime, so a day/night or lights-off switch needs no custom shader or duplicate geometry.
---
**When:** You want a zero-per-frame-cost day/night or lights-on/off switch between two baked states.

**How:**
- Udon whitelists `Renderer.lightmapIndex` and `lightmapScaleOffset` setters (`UnityEngineRenderer.__set_lightmapIndex__SystemInt32__SystemVoid`, plus MeshRenderer/SkinnedMeshRenderer variants). Verified by reflecting over `UdonEditorManager.GetNodeDefinitions()`. `LightmapSettings` / `LightmapData` are **not** exposed — you don't need them.
- Bakery rebinds lightmaps at runtime in builds: `ftLightmapsStorage.Awake()` → `ftLightmaps.RefreshScene()` and `Start()` → `RefreshScene2()` run outside `#if UNITY_EDITOR`, rebuilding the array from the in-scene `storage.maps` list.
- Bake twice; append bake B's atlases to `storage.maps` at edit time (no LightingDataAsset surgery — Bakery's LDA holds probes only); Udon offsets each renderer's `lightmapIndex`.
- Same draw calls and shaders; cost is set B's VRAM. B can be downscaled on import (`lightmapScaleOffset` is normalized) but must stay **BC6H** (Unity decodes it as HDR without a custom shader).

**Pitfalls:**
- Both bakes must produce **identical atlas packing** — vary only light intensity/colour. Never add/remove a `BakeryLightMesh` or change lightmap-static objects between bakes (Bakery skips lightmapping light-mesh objects, so removing one repacks the atlas). Diff every renderer's `lightmapScaleOffset` before/after.
- Hard cut, not a fade (a cross-fade needs a custom two-lightmap shader).
- Not covered: light probes (`LightProbes` not exposed — players keep set-A brightness), emissive materials (toggle via MaterialPropertyBlock), reflection probes.
- Alternatives cost more: a custom two-lightmap shader adds a fetch and material forks; duplicate geometry duplicates the static-batch vertex buffer.
