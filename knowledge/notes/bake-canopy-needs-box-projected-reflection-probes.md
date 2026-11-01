---
title: Closed canopy needs box-projected reflection probes over the woods
topic: probes-reflection-and-light
tags: [reflection probes, box projection, forest, canopy, fog]
summary: Under a closed canopy, surfaces outside every probe box reflect open sky and read cold slate-grey; add box-projected custom probes over the woods and a sky-only default probe, and re-bake them after every lightmap bake and fog change.
---
**Symptom:** a trunk at the end of a woodland path read cold slate-grey (RGB 50,48,41 against 28,24,14 with
reflections off).

**Cause:** no reflection probe covered the woods, so glossy and specular terms sampled the open-sky default probe.

**Fix / rule:** two box-projected probes over the woods, importance 1, blend distance 2 m, resolution 256 (~1 MB each),
plus a sky-only default probe (`cullingMask = 0`, `clearFlags = Skybox`). Bake each with
`Lightmapping.BakeReflectionProbe`, then bind `customBakedTexture` and set `mode = Custom`. Re-bake after every
lightmap bake and after any fog change.

**Verify:** the same trunk pixel before/after and with reflections off; probe file mtimes newer than the lightmaps.
