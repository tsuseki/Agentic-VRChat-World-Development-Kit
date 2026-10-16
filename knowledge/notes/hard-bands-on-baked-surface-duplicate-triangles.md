---
title: Hard flat bands on a lightmapped surface can be duplicate triangles, not normals
topic: geometry-meshes-uvs
tags: [lightmap, uv2, duplicate triangles, z-fighting, smooth shading, weld]
summary: Coincident duplicate triangles force one UV2 chart per triangle and z-fight with different baked values, painting hard bands that look like missing smooth shading.
---
**Symptom:** A lightmapped surface shows hard-edged flat bands ("forgot to shade smooth"), but normals are provably smooth and lightmap resolution is fine.
**Cause:** 544 of 1136 triangles were exact duplicates. Broken topology made the unwrapper emit one chart per triangle (1114 charts / 1136 tris), each baked in isolation; the coincident copies z-fight with different baked values, so the winner flips per pixel.
**Fix / rule:** Sweep every lightmapped renderer for **UV2 charts ÷ triangles**; ~1.0 is the alarm (≈0.5, i.e. 2 tris/chart, is normal per-quad charting on boxy meshes). Dedupe → weld by (position, normal, uv0) → `Unwrapping.GenerateSecondaryUVSet` → full rebake. Welding on position alone destroys genuine hard corners.
**Verify:** Judge with a level-stretched before/after crop; a gradient step-count metric got worse across a fix that plainly worked.
