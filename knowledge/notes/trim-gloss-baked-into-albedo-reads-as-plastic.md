---
title: Gloss painted into an albedo reads as wet plastic at any smoothness; untextured darks need lower values
topic: materials-textures-shaders
tags: [material, albedo, gloss, trim, matte wood, untextured]
summary: A trim material with varnish/piping highlights painted into its albedo looks like chrome even at low _Glossiness; swap to a matte material instead of tuning gloss.
---
**Rules:**
- Some pack "trim" materials paint varnish highlights and light edges into the albedo; they read as wet plastic/chrome even at `_Glossiness` 0.02. Swap the renderers to a matte material (e.g. planks texture, gloss 0.02).
- Highlights that remain after gloss → 0.02 can be diffuse hotspots from nearby lights, not material gloss.
- Untextured materials need roughly **two-thirds** the value of textured ones to read equally dark next to them (walnut example: (0.20, 0.13, 0.085), gloss 0.12).
- Standard metals: moderate values (e.g. metallic 0.45 / gloss 0.18) — higher made a dark iron mirror the skybox; full-metallic gold reads black until reflection probes are baked (see [metallic-materials-cannot-be-judged-before-a-bake](metallic-materials-cannot-be-judged-before-a-bake.md)).
- Replace placeholder primitives (cylinders as bottles, cubes as plants) with real silhouettes; recolouring a primitive does not make it read as the object.
