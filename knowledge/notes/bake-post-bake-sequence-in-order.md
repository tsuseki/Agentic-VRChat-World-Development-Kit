---
title: After a world bake, run the post-bake steps in one fixed order
topic: lighting-baking
tags: [post-bake, reflection probes, bindings, verification, ftGlobalStorage]
summary: Wait for Bakery's finished line, re-bake reflection probes, restore the shared global storage, run the world's bake-dependent rebuilds, verify counts and bindings, then do a guarded save; skipping or reordering steps ships stale probes or broken bindings.
---
**Symptom:** the separate post-bake rules existed, but bakes were saved with stale reflection probes, a modified
project-wide Bakery storage file, or derived data (probe-SH tables, probes-off lever) from the previous bake.

**Fix / rule (in this order):**
1. Wait for the bake to really finish ("Finished rendering" in the log / `bakeInProgress` false and the active scene
   back from `_tempScene`), lightmap files newer than the launch.
2. Reflection probes (cube and box), probe file mtimes newer than the lightmaps.
3. Restore the project-wide Bakery storage if version control tracks it (`git restore -- Assets/Bakery/ftGlobalStorage.asset`)
   unless the change was intended.
4. World-specific re-samples that copy baked data: merged-cell SH tables, the lightmapped-renderers-probes-Off lever,
   any baked depth or AO lookups.
5. Verify: expected lightmap count; every lightmapped renderer has an index; 0 negative or non-finite scale-offsets;
   Light Volume count and textures non-null; 0 non-Baked lights; renderers of re-imported prefabs bound.
6. Guarded save: active scene path is the world scene, play mode off, `MarkSceneDirty` then save; then commit.

**Verify:** keep the verify step's numbers in the bake report next to the lightmap and probe timestamps.
