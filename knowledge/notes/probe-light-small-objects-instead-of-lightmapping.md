---
title: Move small objects to light probes instead of fighting overlapping-UV warnings
topic: lighting-baking
tags: [receiveGI, LightProbes, overlapping UVs, small objects, lightmap, ContributeGI, texel density]
summary: Unity's overlapping-UV warning on small trim cannot be fixed by pack margin; keep ContributeGI but set receiveGI to LightProbes for renderers under ~1.3 m.
---
**Symptom:** Unity warns "There are N objects in the Scene with overlapping UV's" and the count grows as the world fills with furniture (52 -> 827). Regenerating UV2 with a fatter `packMargin` (e.g. 0.035) barely moves it.

**Cause:** At 16 texels/unit a 5 cm mullion, a 4 cm bulb or a 30 cm furniture leg gets a chart a couple of texels across, and Unity's own padding overlaps it. No margin rescues a 2-texel chart; these objects are too small to deserve a lightmap.

**Fix / rule:** Keep `ContributeGI` (they still occlude, cast baked shadows, and emissive ones still inject light) but stop lightmapping them:

```csharp
var gi = typeof(MeshRenderer).GetProperty("receiveGI");   // via reflection
gi.SetValue(r, System.Enum.Parse(gi.PropertyType, "LightProbes"));
```

Rule that worked: **`renderer.bounds` max dimension < 1.3 m -> probe-lit.** 994 of 1,643 renderers moved in one pass; shell, floors, ceilings, partitions, columns, decks and long railing runs kept their lightmaps. Texel demand barely changed but 994 fewer charts had to be packed and the overlap warnings vanished.

**Verify:** Check light-probe coverage for the newly probe-lit set, and that `ReflectionProbeStatic` is untouched (separate flag). For larger objects with the same warning, see [overlapping-lightmap-uv-warning-is-a-gutter-problem](overlapping-lightmap-uv-warning-is-a-gutter-problem.md); for big objects wrongly on probes, see [check-receivegi-before-adding-lights](check-receivegi-before-adding-lights.md).

Related: [glass-should-be-probe-lit-not-lightmapped](glass-should-be-probe-lit-not-lightmapped.md), [reflection-probes-need-reflectionprobestatic-flag](reflection-probes-need-reflectionprobestatic-flag.md)
