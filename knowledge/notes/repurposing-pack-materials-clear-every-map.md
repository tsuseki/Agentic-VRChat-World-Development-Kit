---
title: When repurposing a pack material, clear every map, not just _MainTex
topic: materials-textures-shaders
tags: [materials, atlas, _SpecGlossMap, _BumpMap, _MainTex, Autodesk Interactive, tiling, non-uniform scale]
summary: On atlas materials the roughness and normal maps carry the design itself, so replacing only the albedo leaves the old pattern visible, and a bound _SpecGlossMap makes the smoothness slider dead.
---
**Symptom:** Hallway runners read as "poured concrete or granite, not textile". After assigning a new seamless woven albedo and dropping smoothness 0.50 -> 0.04, the rugs still showed the old designs (soft rectangles and circles) and still looked glossy.

**Cause:** The material (shader Autodesk Interactive) still had `_SpecGlossMap` and `_BumpMap` bound to the pack's rug-atlas roughness and normal maps. On a multi-design atlas those maps encode **the artwork of every rug in the sheet**, so roughness and normal painted the old pattern over the new albedo. And with `_SpecGlossMap` bound, the `_Glossiness` float is ignored entirely.

**Fix / rule:** When repurposing a pack material, clear the whole map set: `_SpecGlossMap`, `_MetallicGlossMap`, `_BumpMap`, `_OcclusionMap`, `_Detail*`, and disable `_SPECGLOSSMAP` / `_METALLICGLOSSMAP` / `_NORMALMAP`. Then the scalar sliders take effect.

**Diagnose:** Dump every texture slot (`shader.GetPropertyCount()` filtered to `ShaderPropertyType.Texture`). `m.mainTexture` reports only `_MainTex`, which was correct all along.

**Pitfalls:**
- An atlas-UV-mapped mesh with a real-world tiling scale makes each UV shell sample a different design. For flat runners, replace the mesh with a plain scaled cube and set `_MainTex_ST` per renderer from world bounds.
- A root with `rotY 90` **and** non-uniform `localScale (0.53,1,1)` cannot represent an identity-rotation child; a box built there came out 7.48 x 0.86 m instead of 4.00 x 1.60 m. Neutralise the root (`localScale = 1`, identity rotation) and rebuild children in world space.

See also [standard-shader-maps-override-scalars](standard-shader-maps-override-scalars.md).
