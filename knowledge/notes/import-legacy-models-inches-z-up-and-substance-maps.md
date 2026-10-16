---
title: Import legacy models: inch units, Z-up roots, missing MTLs and Substance roughness
topic: import-fbx-prefabs
tags: [import scale, 3ds Max, inches, Z-up, Substance, roughness, smoothness, UV2]
summary: A 3ds Max OBJ in inches needs globalScale 0.0254; Z-up FBX roots need a baked -90° X in a placement-ready prefab; Substance roughness must be inverted into Unity smoothness.
---
**How:**
- 3ds Max exports in inches (e.g. 74.6 units tall): `globalScale = 0.0254`.
- Z-up FBX (imports lying down; root may also carry odd scale like 0.88): build a placement-ready prefab with floor-centre pivot, baked `Euler(-90,0,0)`, materials assigned. Place the prefab, never the raw model.
- OBJ referencing a missing `.mtl`: assign the texture manually on a new material via the importer remap.
- Substance exports (`BaseColor / Metallic / Roughness`): Unity Standard needs smoothness = 1 − roughness. Combine into one `MetallicSmoothness` texture (RGB = metallic, A = 255 − roughness), sRGB **off**. `Texture2D.LoadImage` on the source PNG bytes bypasses importer readability. Or use a roughness-input shader.
- Check the texture set is complete (a normal map may never have been exported).
- Enable `generateSecondaryUV` on models without UV2 before baking.
- Keep heavy sources (`.blend`, `.spp`, layered PSDs) in a folder outside `Assets/`.
