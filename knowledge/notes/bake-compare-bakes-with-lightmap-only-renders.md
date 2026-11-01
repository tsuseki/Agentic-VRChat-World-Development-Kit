---
title: Compare two bakes with lightmap-only renders, not beauty renders
topic: lighting-baking
tags: [bake comparison, replacement shader, pixel diff, atlas size]
summary: Beauty renders of two bake variants differed by ~18 % for every variant (wind, LOD fade, textures); a replacement shader that outputs only the lightmap (with alpha clip) and the % of pixels more than 24/255 off ranks the variants.
---
**Symptom:** same-camera beauty renders of a world against its source scene stayed ~18 % different for every bake
variant tried, so they could not rank atlas sizes.

**Fix / rule:** render each pose with a replacement shader that outputs only the decoded lightmap (`unity_Lightmap`
at `uv2 * lightmapScaleOffset`), keeping the cutout alpha clip so leaves keep their shape, and report the % of pixels
more than 24/255 off. Keep the pose list as a file so every variant uses the same cameras.

**Verify:** a variant compared with itself gives 0 %; the known-worse variant ranks worse.
