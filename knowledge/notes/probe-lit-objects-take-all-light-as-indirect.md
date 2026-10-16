---
title: Probe-lit objects get all light as indirect: AO hits everything and brightness differs from lightmapped neighbours
topic: probes-reflection-and-light
tags: [light probes, non-static, ambient occlusion, _OcclusionStrength, decals, albedo, BakeryLightMesh]
summary: On a non-static probe-lit object, Standard's occlusion applies to its entire lighting and its albedo-to-render ratio differs from the lightmapped ground beside it — and rebaking fixes neither.
---
**Symptom:** Probe-lit scenery (`lightmapIndex = -1`, `receiveGI = LightProbes`) under a Baked sun: albedo tuning oscillates without converging; photoscan crevices render as black "cave mouths" a reviewer reads as open shells; decals don't match the ground they sit on.

**Cause:**
- Standard applies `_OcclusionStrength` to *indirect* diffuse. A probe-lit object has no direct component, so a baked AO map (reaching 0.000 on photoscans) crushes **all** of its light. Proof: albedo floor L 0.260 with no texels below, yet render Lmin 0.000; rendered darkness anti-correlated with albedo darkness.
- A probe-lit decal and lightmapped ground beside it render at **different fractions** of their albedo, and the size and even sign of the gap is local to each site's probe coverage (measured on one map: ~1.9×, ~1/8, and 0.832 at three sites). Never import a ratio from another site; a gamma model predicted 1.50 where the truth was 1.24.

**Fix / rule:**
- Drop occlusion to ~0.25–0.3 (or remap the AO map 0..1 → ~0.55..1). Before declaring a photoscan open, weld verts by position and count boundary edges.
- Measure decal compensation: mask the decal, top-down ortho render, compare its mean to adjacent ground. Re-measure after any bake.
- First ask whether the object should be non-static at all — immovable scenery under a Baked sun normally should be lightmap-static. But a uniform flag across a whole subtree is evidence of intent; find out why before flipping. On Bakery maps `ContributeGI` alone yields no lightmap — it must also join a Bakery group.
- To dim a blown-out glowing probe-lit prop, lower its **albedo**; emission is nearly dead as a knob when the prop sits in the hot pocket its own light mesh baked (killing emission moved 0.699 → 0.671; albedo ×0.64 → 0.438). Toggling Baked lights at runtime changes nothing.

**Verify:** a control in one frame — two siblings on the same material pipeline, one clean one not. If albedo darkness doesn't predict rendered darkness, the defect is in another texture slot.
