---
title: ProBuilder meshes have no UV2 until Optimize(pb, true); Lightmapping.lightingSettings throws when unset
topic: lighting-baking
tags: [ProBuilder, UV2, lightmap UV, LightingSettings, scripted bake, scaleInLightmap]
summary: pb.Refresh() never generates lightmap UVs, so ProBuilder rooms bake off overlapping auto-UVs; and the lightingSettings getter throws rather than returning null.
---
**Symptom:** A ProBuilder-built room bakes slightly blotchy (easy to blame on sample counts); or a scripted bake setup crashes on a null check.

**Cause / Fix:**
1. `pb.Refresh()` rebuilds geometry and UV0 but **not** UV2. A room from `ShapeGenerator.GenerateCube` had UV2 on 0 of 94 GI renderers, so every surface sampled its neighbours' light.
   ```csharp
   UnityEditor.ProBuilder.EditorMeshUtility.Optimize(pb, true);   // true = force rebuild UV2
   ```
   Thin trim (mullions, sills, coves, frames) can still report overlapping UVs because islands land sub-texel. Do not raise `scaleInLightmap` on them (a blunt ×2.5 more than doubled atlas demand): pieces under ~1.3 m largest dimension go to `receiveGI = LightProbes` ([probe-light-small-objects-instead-of-lightmapping](probe-light-small-objects-instead-of-lightmapping.md)); larger ones get a wider `packMargin` ([overlapping-lightmap-uv-warning-is-a-gutter-problem](overlapping-lightmap-uv-warning-is-a-gutter-problem.md)).
2. `Lightmapping.lightingSettings` **throws** (`Lightmapping.lightingSettings is null...`) when none is assigned, so a null check on the getter is itself the crash. Create and assign first:
   ```csharp
   var ls = AssetDatabase.LoadAssetAtPath<LightingSettings>(path);
   if (ls == null) { ls = new LightingSettings(); AssetDatabase.CreateAsset(ls, path); }
   // ...configure...
   Lightmapping.lightingSettings = ls;
   ```
   Objects created earlier in the same script body survive the throw, so make re-runs idempotent (destroy-then-recreate).

**Verify:** before any bake, check `mesh.uv2 != null && mesh.uv2.Length > 0` per renderer and print ok/fail counts. A UV2-less bake isn't worth reviewing.
