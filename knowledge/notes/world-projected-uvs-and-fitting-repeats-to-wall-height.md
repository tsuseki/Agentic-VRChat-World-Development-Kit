---
title: Use world-projected UVs for uniform tiling and fit one texture repeat to the wall height
topic: materials-textures-shaders
tags: [UV, world-projected, tiling, texel density, wall panels, mainTextureScale]
summary: Generate floors/walls as single meshes with UVs = world position / repeat size so density is uniform; for panelled wall textures set scale.y = 1/height and offset so one repeat spans the wall exactly.
---
**How:**
- Replace many blockout cubes with one mesh (e.g. a sweep-line union of street rectangles, 39 quads) whose UVs are **world-projected**: `uv = worldXZ / 3` for 3 m per repeat on floors; box-projected at 2 m for walls. Material tiling stays 1,1 — the mesh carries density, so changing repeat size means regenerating UVs.
- Add UV2 (normalized planar, or `GenerateSecondaryUVSet`) so the mesh is bake-ready.
- Collision can stay on separate invisible boxes (renderer and filter stripped) while one visual mesh draws the wall in one draw call.
- Panelled/frieze wall textures: `mainTextureScale.y = repeats / wallHeight`-style fit so exactly one repeat spans the wall, `offset.y = −minY / wallHeight`. E.g. a 6 m wall with world-UV v = y/2: scale (0.5, 1/3), offset (0, 2/3). Recompute if wall heights change; clone the material per wall height.
- Wood veneer on world-UV walls: rotate the texture 90° so the grain runs vertical.
- Stage/frame panels added later must use the same UV formula (e.g. `u = (x + c)/2, v = y/2`) to continue the pattern.
