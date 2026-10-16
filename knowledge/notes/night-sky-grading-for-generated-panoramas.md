---
title: Grading a generated night panorama: prompt for true night, protect lights by local contrast, elliptical stars
topic: materials-textures-shaders
tags: [skybox, night, grading, stars, equirectangular, HDR, BC6H]
summary: Orange-lit-cloud wording pulls toward dusk; protect city lights by local contrast not raw luminance; draw stars as ellipses widened by 1/cos(elevation) after upscaling.
---
**How:**
- Prompt: "orange-grey haze / clouds lit orange from below" pulls toward evening. For true night add "deep night, moonless pitch-black sky, no twilight, no sunset glow, dark blue-black sky from horizon to zenith, city lights are the only illumination" and drop orange-cloud language.
- Darken the sky but protect lights by **local contrast** (`lum − boxblur24(lum) > 0.04`), never raw luminance (that protects the haze wash itself). Curve by degrees above horizon: 1.0 at 0°, 0.45 at 5°, 0.2 at 9°, 0.12 at 15°+; desaturate the remaining unprotected sky 35 %.
- **Stars:** in equirect they must be ellipses to look round on the sphere: x-sigma × 1/cos(elevation), cap elevation ~78°, ~80 stars, angular sigma 0.055–0.10°, HDR boost ×2 on top of the tonemap so BC6H compression and mips keep them. Draw after any ESRGAN upscale (it smears them).
