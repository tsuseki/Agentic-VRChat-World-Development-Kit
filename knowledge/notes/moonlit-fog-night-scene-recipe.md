---
title: Recipe for a moonlit, misty night look in the Built-in pipeline
topic: lighting-baking
tags: [night, fog, skybox, moon, value ordering, terrain, BIRP]
summary: Get the 'dark silhouettes in glowing mist' night look by ordering values (ground < vegetation < fog < sky horizon), dimming lights rather than materials, and using a gradient skybox whose below-horizon colour equals the fog colour.
---
**When:** A moonlit foggy night scene in Unity Built-in RP (large outdoor terrain with trees).

**How:**
- **Value ordering is the whole trick:** ground textures (darkest) < vegetation silhouettes < fog colour < sky horizon glow. Fog colour is lighting-independent, so it becomes the luminous mist once everything lit is darker than it. If trees read pale against bright ground, the ordering is inverted; fix scene values instead of fighting the fog.
- **Dim the lights, not the materials:** moon directional ~0.4 intensity, ambient ~0.28. Many tree shaders have no albedo tint property, only translucency (set e.g. `_TranslucencyStrength 0`).
- Pre-darken ground albedos to mean luminance ~0.06-0.15 (regrade the textures in place; forest floor darkest).
- **Skybox/Procedural is unusable here:** its horizon glow depends on sun azimuth and makes bright wedges. Use a custom gradient skybox whose below-horizon colour **exactly equals the fog colour**, so a finite terrain band fades into sky in every direction. Horizon band ≈ fog x 1.7, azimuth-uniform.
- Bake the moon disc and halo into the skybox shader; a scene-quad moon gets eaten by fog. Drive it with `_MoonDir = -moonLight.transform.forward`.
- Terrain-painted trees are never baked as shadow casters (Bakery or Unity). Stamp directional shadow streaks into a per-terrain mask texture and multiply it into albedo in a modified terrain shader.

