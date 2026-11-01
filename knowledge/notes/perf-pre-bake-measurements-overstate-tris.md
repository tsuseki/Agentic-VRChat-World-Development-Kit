---
title: Before the first bake a Baked sun still renders realtime shadows; don't budget from it
topic: performance
tags: [pre-bake, shadows, triangles, Baked light, UnityStats]
summary: A scene with a Baked sun but no bake renders realtime shadow passes (7.88 M tris vs 2.6 M after the bake); measure triangle budgets after the bake, and read play-mode tris on static batches as combined-mesh counts.
---
**Symptom:** a world's worst pose read 7.88 M triangles before its first bake and 2.6 M after.

**Cause:** Unity lights a Baked light by its `bakingOutput`; with no bake it renders realtime, including shadow-caster
passes over the whole visible scene.

**Fix / rule:** take budget numbers only after a bake (or after copying a baked sibling's `bakingOutput`). In play mode
`UnityStats` triangles on statically batched props count the combined meshes; count per-object tris in edit mode.

**Related:** [new-baked-lights-render-realtime-until-bakingoutput-set](new-baked-lights-render-realtime-until-bakingoutput-set.md).
