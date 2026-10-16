---
title: Import 8K equirect HDRI skyboxes at 2048 and don't expect import settings to fix photographic softness
topic: materials-textures-shaders
tags: [hdri, skybox, cubemap, import size, BC6H, ffmpeg, night city]
summary: An 8192×4096 HDRI needs a 2048 cubemap face to carry its detail (1024 looks blurry through big windows); softness baked into the photo needs real geometry for a crisp skyline.
---
**When:** Using an equirectangular HDRI (e.g. a night-city skyline) as the skybox behind large glazing.
**How:**
- Source 8192×4096 = 22.75 px/degree; a 90° cubemap face needs exactly 2048 px. Import at `maxTextureSize` 2048: BC6H ≈ 64 MB vs 16 MB at 1024. 1024 throws away half the detail; above 2048 is waste.
- Preview many HDRIs without importing: ffmpeg decodes Radiance `.hdr` (`ffmpeg -i in.hdr -vf scale=480:-1 out.png`) — build a contact sheet and also check for artifacts (e.g. a magenta smear at the nadir).
- For a high-rise interior, pick HDRIs shot from rooftop height (horizon at or below camera).
**Pitfalls:**
- Many HDRI packs are shot with shallow depth of field (bokeh discs on lights). No import setting or pack-mate fixes that. For a crisp skyline, build real geometry towers (emissive window grids on boxes), which also give parallax; keep the HDRI as the far backdrop.
- Laplacian focus variance tracks how much high-contrast detail fills the frame, not focus — compare native 1:1 crops by eye.
- Rule out the glass first: hide every pane and re-shoot before touching import settings.
