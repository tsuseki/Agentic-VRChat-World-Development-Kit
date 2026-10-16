---
title: A prop added after the last bake reads blue - check lightmapIndex before re-tinting
topic: lighting-baking
tags: [lightmapIndex, unbaked, ambient, skybox, new-props, review-mode]
summary: lightmapIndex -1 means no baked data, so a new prop falls back to skybox ambient and reads cold next to an identical baked one; do not re-tint the material.
---
**Symptom:** A new prop with exactly the same material as its neighbour 30 cm away renders cold blue-grey while the neighbour renders warm.

**Cause:** The new prop wasn't in the last bake. `MeshRenderer.lightmapIndex == -1` means no baked lighting data at all, so it falls back to ambient - under a night skybox, blue. The neighbour reported `65534` (0xFFFE = lit by probes, data valid) and picked up warm baked bounce. Bright materials hide it; mid-tone warm materials expose it worst.

**Fix / rule:**
- Check `lightmapIndex` before touching a material. -1 means "not baked yet", not "wrong colour". Re-tinting produces a prop that is wrong as soon as the bake lands.
- Review anything placed since the last bake in composition-only mode and state explicitly that colour and exposure are not judgeable yet.

Related: [metallic-materials-cannot-be-judged-before-a-bake](metallic-materials-cannot-be-judged-before-a-bake.md)
