---
title: Grass and small ground cover as bake casters print texel-sized smudges; darken the base in the shader instead
topic: lighting-baking
tags: [grass, ground cover, shadow casters, lightmap resolution, _BaseShade, probe-lit, contact shadow]
summary: Thousands of sub-metre grass casters bake blotchy lightmap-texel smudges and darken the probes inside the grass; switch them to non-casting and get contact shading from a vertex-height base-darkening term on a world-owned material copy.
---
**Symptom:** After a bake in which grass tufts and other small ground cover (roughly < 0.8 m tall) were shadow casters, the soil showed dark, soft, blocky smudges that did not match any tuft ("grass shadows look bad, the resolution does not work"); the grass itself, being probe-lit, read darker than before the bake.

**Cause:** A lightmap texel is typically 10-30 cm on large outdoor ground, larger than a tuft. A caster smaller than a few texels cannot print a shaped shadow; it prints a smear whose shape is the texel grid. The same casters also occlude the light probes sampled inside the grass, so probe-lit grass inherits the darkening. Casting grass was originally switched on to give "contact shadow", but at this scale the result is noise, not contact.

**Fix / rule:**
- Every grass and small ground-cover source renderer gets `shadowCastingMode = Off` (set it on the source renderers, so it survives later merges into cell meshes). Keep shrubs, trees and any plant that casts a readable shape (about 0.8 m and taller, woody) as casters.
- Get contact shading from the shader: a vertex-height base-darkening term (here `_BaseShade` strength, `_BaseShadeHeight` height over which it fades) on **world-owned copies** of the grass materials, never on the pack originals. Tune by eye at eye height and at 5-15 m. A strength near 1.0 turns isolated tufts into black holes; ~0.9 with a ~0.7 fade height read as soft contact.
- Check the pack material first: it may already carry a non-zero base-shade value.
- If seats or props must stay clear of grass, disable the source renderers inside a margin and scale a feather ring (x 0.6-1) instead of editing the merged cells; keep an undo log of the changed renderers.

**Pitfalls:** Probe-lit grass reads brighter once its own occlusion leaves the baked probes (about +15-27 % mean image luminance in grassy views). That is the pre-caster state, not a regression; compare against a pre-caster capture, not the casting bake. An A/B of the borderline classes needs a second bake; decide by the rule "it is grass".

**Verify:** same-camera before/after at eye height, 5 m and 15 m over a grass field and a slope (2x crops): no texel-sized smudges on the soil, grass roots darker than tips, no black holes under single tufts; report the mean-luminance change honestly.

Related: [probe-lit-grass-ignores-baked-shadows](probe-lit-grass-ignores-baked-shadows.md), [perf-merging-clumps-needs-vertex-pulling-for-bundle-size](perf-merging-clumps-needs-vertex-pulling-for-bundle-size.md)
