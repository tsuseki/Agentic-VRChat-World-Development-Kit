---
title: Bakery ignores Unity environment lighting — add a BakerySkyLight or roofed shade bakes black
topic: lighting-baking
tags: [Bakery, BakerySkyLight, ambient, skybox, outdoor]
summary: Unity ambientMode=Skybox is irrelevant to a Bakery bake and ambient is not added on top of lightmaps at runtime; open shade looks fine from bounce while roofed shade goes black.
---
**Symptom:** areas under a roof bake pure black while open shade looks fine (lit ground bounces into it), so it reads like a material or occluder bug.

**Cause:** Bakery does not inherit Unity's environment lighting, and ambient is not added at runtime on top of a lightmap.

**Fix / rule:** add a `BakerySkyLight`. One that matched the sky: `cubemap` = the skybox's own cubemap (`RenderSettings.skybox.GetTexture("_Tex") as Cubemap`), `hemispherical = true` (no light from below the horizon), `bakeToIndirect = true`. The Unity directional light is picked up by Bakery without a `BakeryDirectLight` component — sun shadows bake with none present.
