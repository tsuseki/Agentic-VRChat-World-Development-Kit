---
title: ProBuilder auto-UVs tile screens, artwork and signs — remap UVs and strip ProBuilderMesh
topic: geometry-meshes-uvs
tags: [probuilder, uv, video screen, signage, tiling, content texture]
summary: ProBuilder Auto UVs are world-scaled (~1 unit/m), so a content texture on a 4.4 m screen repeats in a grid; remap to 0..1 and remove the ProBuilderMesh component or a refresh restores the bug.
---
**Symptom:** A video screen/artwork/sign shows its image repeated in a grid (e.g. 5×3). Tiling materials on the same kind of faces look fine, so it goes unnoticed.
**Cause:** ProBuilder faces default to world-scaled Auto UVs; a 4.4 m quad has `uv.x` spanning −1.70..2.70.
**Fix / rule:**
- Sweep the class: every renderer whose material is a screen/art/video/sign — check `mesh.uv` min/max against 0..1. One reported screen became nine.
- `Instantiate` the mesh (don't edit a shared asset), remap UVs to fill 0..1 by projecting the two widest local-bounds axes, then **remove the `ProBuilderMesh` component** — otherwise ProBuilder rebuilds from its auto-UV data on the next refresh.
- Check `uv2` survived and re-assert `ContributeGI`.
- Clamp wrap mode is not a fix: UVs outside 0..1 smear edge pixels.
- Get horizontal direction right too (see [wall-panel-uv-handedness-sibling-check](wall-panel-uv-handedness-sibling-check.md)).
