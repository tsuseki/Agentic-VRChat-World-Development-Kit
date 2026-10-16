---
title: Baked reflection probes capture only renderers flagged ReflectionProbeStatic
topic: probes-reflection-and-light
tags: [reflection-probe, static-flags, ContributeGI, ReflectionProbeStatic, cubemap, md5]
summary: ContributeGI and ReflectionProbeStatic are independent flags; renderers without ReflectionProbeStatic are invisible to baked reflection probes, which then capture only the sky, and the tell is byte-identical cubemaps.
---
**Symptom:** In a warm night interior, smooth materials look muddy or marble reads as a black mirror. Every health check passes: the bake succeeds, probes have valid `.exr` assets, `rp.bakedTexture` is non-null.

**Cause:** `StaticEditorFlags.ContributeGI` and `StaticEditorFlags.ReflectionProbeStatic` are separate. The Static dropdown's *Everything* sets both, but a scripted `SetStaticEditorFlags(go, ContributeGI)` drops reflection capture - the probes render the skybox and nothing else, so every smooth material gets cold sky specular. You then tune materials and lights that were never the problem.

**Verify (oracle):** md5 the cubemaps.
```bash
md5sum Assets/Scenes/<Scene>/ReflectionProbe-*.exr
```
Probes at different positions in a furnished room cannot produce identical files. Identical hashes across probes = all captured pure sky = no renderer has the flag. (The highest-numbered one is the skybox ambient probe and legitimately differs.) After the fix all hashes must differ.

**Fix / rule:**
```csharp
var f = GameObjectUtility.GetStaticEditorFlags(go);
GameObjectUtility.SetStaticEditorFlags(go, f | StaticEditorFlags.ReflectionProbeStatic);
```
Then re-bake only the probes (seconds, no relight):
```csharp
foreach (var rp in Object.FindObjectsOfType<ReflectionProbe>(true))
    Lightmapping.BakeReflectionProbe(rp, AssetDatabase.GetAssetPath(rp.bakedTexture));
```
`Lightmapping.BakeAllReflectionProbes()` does not exist in 2022.3; per-probe `BakeReflectionProbe(probe, path)` is the public API. Re-bake reflection probes after every lightmap bake.

**Leave the flag off:** glass/transparent panes (double-reflect, can occlude the view), video/TV screens (capture freezes one frame), small dressed props (capture cost for nothing). `SetStaticEditorFlags` does not walk children - see [static-editor-flags-do-not-propagate-to-children](static-editor-flags-do-not-propagate-to-children.md). Related: [baked-reflection-probe-lost-on-reload-with-bakery](baked-reflection-probe-lost-on-reload-with-bakery.md)
