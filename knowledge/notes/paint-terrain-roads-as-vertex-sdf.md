---
title: Paint roads onto a terrain mesh as a vertex-colour signed distance, thresholded in the shader
topic: geometry-meshes-uvs
tags: [terrain, road, signed distance field, vertex colour, shader, blender export]
summary: Store signed distance to the road edge per vertex and threshold per pixel; edge error is the sagitta (~3 cm on a 5 m grid), while per-face material painting staircases at cell size.
---
**When:** Painting a road/path or any hard-edged region onto a generated terrain mesh without separate geometry.
**How:**
- In Blender write `Col.r = clamp(sd/20 + 0.5, 0, 1)` (signed distance to edge, ±20 m range); more regions in other channels.
- Shader decodes `sd = (c - 0.5) * _SDRange` and blends with `saturate(0.5 - sd/_EdgeSoft)`.
- Linear interpolation of a distance field across a triangle is exact, so the edge is a chord of the true curve; deviation ≈ cell²/(8·radius) ≈ 3 cm for a 5 m grid at a 100 m-radius bend.
- Export FBX with `colors_type='LINEAR'` — the channel is data; an sRGB curve shifts the 0.5 threshold. Verify in Unity via `mesh.colors32`.
- Tile layer textures by world-space XZ in the shader: no usable UV0 needed, seamless across chunks, uv2 free for lightmaps. Collapses several submeshes to one material per chunk.
**Pitfalls (don't retry):**
- Per-face `material_index` on a 5 m grid staircases in full cell steps.
- Snapping boundary vertices onto the true edge before classifying faces by centroid: most staircase-corner vertices are beyond tolerance; the staircase survived.
- Preview with an equivalent Blender node material in EEVEE; Workbench ignores it and shows bare ground.
