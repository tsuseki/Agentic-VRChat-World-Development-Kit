---
title: Relight unlit ordinary props with a synthetic SH probe, not emission
topic: probes-reflection-and-light
tags: [LightProbeUsage.CustomProvided, SH, unity_SHAr, MaterialPropertyBlock, emission, Udon]
summary: For a renderer left with no lightmap and no probe, dim emission suits only emitters; ordinary props need CustomProvided SH in a property block so they shade by normal and albedo.
---
**Symptom:** Props relit with a dim `_EmissionColor` property block pass a luminance check but look wrong: a plant becomes a flat formless cut-out, near-black plastic has to glow to match its neighbours.

**Cause:** Emission ignores the surface normal and ignores albedo. The defect is missing form, not missing brightness.

**Fix / rule:** Split the list by what the object is. Emitter: dim emission. Ordinary prop: `LightProbeUsage.CustomProvided` plus SH coefficients in the same `MaterialPropertyBlock`, so the shader shades per normal from its own albedo. Both `MaterialPropertyBlock.SetVector` and `CustomProvided` are Udon-exposed and compile under UdonSharp.

SH packing: `unity_SHAr/Ag/Ab` are `(x, y, z, w)` with `w` the constant and `xyz` the linear terms, so a sky/ground gradient is `(0, grad, 0, base)` per channel; `unity_SHBr/Bg/Bb/SHC` are zero. Example dim night values: sky (0.025, 0.033, 0.051), ground (0.007, 0.009, 0.013).

**Scale per renderer, not globally:** local irradiance varies (0.023 on one shelf vs 0.003 in another corner, so one global SH lit a plant ~8x brighter than the dresser under it). Scale = local irradiance / probe irradiance, where local irradiance = a neighbouring lightmapped surface's measured luminance / its albedo luminance (median of the 3 nearest).

**Pitfalls:** Find the class by query (`lightmapIndex == -1 && lightProbeUsage == Off`), not from a reviewer's list (32 found vs 10 named). When measuring a prop against the surface behind it, fix the viewpoint convention; a "best angle" search can put a bright window behind it and change the ratio threefold with nothing changed.
