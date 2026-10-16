---
title: Script-generated meshes need RecalculateTangents or normal maps silently die
topic: geometry-meshes-uvs
tags: [Mesh, tangents, RecalculateTangents, normal map, generated mesh, terrain blend]
summary: A Mesh built in C# has no tangents unless you call RecalculateTangents, so a normal-mapped shader renders it smooth, pale and slightly shiny while albedo measures correct.
---
**Symptom:** Script-generated ground dressing (drifts, aprons, skirts) wearing the same normal-mapped material as the terrain renders as a pale, grainless, faintly shiny plate. Mean tone matches the terrain within 2 %, so reviewers call it "flat untextured pad" or "smooth plaster" and you look at texture or albedo. It survives a rebake unchanged.

**Cause:** `new Mesh()` with `vertices`/`triangles`/`uv` set has an **empty tangent array** unless you call `RecalculateTangents()`. The tangent basis is degenerate, so the normal map (and any detail normal that provides surface grain) contributes nothing.

**Fix / rule:** In every generator whose mesh will wear a normal-mapped shader, call `m.RecalculateTangents()` before assigning. This is not a lighting fix, so no rebake is needed. Sweep the whole generated-mesh family at once; these bugs come in tens.

**Pitfalls:** It hides behind the "unbaked props look pale until the bake" explanation, which is plausible and wrong here.

**Verify:** When generated surfaces read pale, grainless or subtly shiny against what they should match, check `mesh.tangents.Length` first, before albedo, tiling or the bake.
