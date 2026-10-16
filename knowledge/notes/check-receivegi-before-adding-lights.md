---
title: Check receiveGI before adding lights to a black object
topic: probes-reflection-and-light
tags: [receiveGI, light probes, baked light, black silhouette, lightmapIndex, review]
summary: A Baked light never lights a probe-lit renderer directly, so when objects read as black silhouettes despite lights aimed at them, query receiveGI first and move large ones onto the lightmap.
---
**Symptom:** A review lists several features (lift doors, speaker towers, a media wall, hallway canvases) as flat black silhouettes. The obvious fix, and the reviewer's first suggestion, is "more light".

**Cause:** A `Baked` light illuminates lightmapped geometry and, coarsely, nearby light probes. It never lights a probe-lit renderer (`receiveGI = LightProbes`, `lightmapIndex 65534`) directly. Such an object in a probe dead zone stays black no matter how many spots you aim at it, and every wrong attempt costs a full bake. In one scene 2288 renderers were on the probe path by default.

**Fix / rule:**
- First query `receiveGI` on the reported objects, before aiming a light, touching intensity or re-baking:

```csharp
foreach (var r in UnityEngine.Object.FindObjectsOfType<MeshRenderer>())
  if (r.receiveGI == ReceiveGI.LightProbes) /* count / list by parent */;
```

- If it is `LightProbes` and the object is bigger than ~0.12 m, move it to the lightmap (`receiveGI = Lightmaps` plus `ContributeGI`). Moving 37 objects let the already-baked lights reach them. Genuinely tiny parts (0.035-0.114 m) stay on probes; no pack margin helps below ~0.12 m (see [overlapping-lightmap-uv-warning-is-a-gutter-problem](overlapping-lightmap-uv-warning-is-a-gutter-problem.md)).
- Scope: this applies to objects that have (or can get) a clean UV2. Furniture without UV2 can't be lightmapped; keep it on probes but make it a shadow caster (see uv2-less-props-can-cast-baked-shadows-with-receivegi-lightprobes).
- `lightmapIndex` is only meaningful right after a bake; do not read it off a scene that has not been baked since the change.

Related: [probe-light-small-objects-instead-of-lightmapping](probe-light-small-objects-instead-of-lightmapping.md), [unlit-props-need-a-synthetic-sh-probe-not-emission](unlit-props-need-a-synthetic-sh-probe-not-emission.md)
