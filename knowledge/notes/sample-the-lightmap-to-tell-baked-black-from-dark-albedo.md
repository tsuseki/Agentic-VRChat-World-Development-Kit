---
title: Sample lightmap irradiance per submesh to tell "baked black" from dark albedo
topic: lighting-baking
tags: [lightmap, irradiance, albedo, diagnosis, BC6H, uv2]
summary: A floor reading 98% dark in screenshots had normal irradiance — it was dark carpet; read the lightmap texels under each submesh before blaming occluders.
---
**Symptom:** a floor band reads ~98 % dark (mean 0.032) while walls and furniture above are lit — looks like an occluder baked the floor black.

**How:**
- `Graphics.Blit(lightmapColor, RenderTexture ARGBFloat)` (BC6H blocks `GetPixels`) → `ReadPixels`.
- For each triangle map its uv2 centroid through `renderer.lightmapScaleOffset` (`U = u.x * so.x + so.z`, same for V) and read the texel.
- Report mean/max irradiance **per submesh**. Comparable floor vs wall irradiance (0.069 vs 0.096 here) means light arrived and the albedo is dark (carpet ~0.16 vs wall ~0.39 luminance-albedo).

**Fix / rule:** if irradiance is fine, adjust albedo, not lighting or occluders.

**Pitfalls:** "is that sky or an artifact" in a reflection/ceiling — render the pose with `clearFlags = Skybox` and again with a solid magenta clear and no skybox. **Identical mean luminance ⇒ zero sky pixels** (it was denoiser blotch). Confirm with a per-submesh face-normal dump (up/down/horizontal) that a ceiling face exists.
