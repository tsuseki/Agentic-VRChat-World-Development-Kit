---
title: One-atlas tree layout: four 3:4 portrait spray cells plus a bark strip that repeats in V
topic: materials-textures-shaders
tags: [trees, atlas, leaf cards, bark, wrap mode, one material, UV, normal maps, VR]
summary: A square 2048² atlas with four 3:4 portrait spray cells and a vertical bark strip (wrap U Clamp / V Repeat) lets any shader tile bark with plain UVs in one material; cards take the cell aspect so sprays aren't squeezed; a square bark tile with cut UVs cost +47–92 % tris or 4× blurrier bark.
---
**Symptom:** Putting a low-poly tree on one material for a third-party foliage shader (one texture slot, no separate bark material) forced a choice: bark in a square atlas tile needed its UVs cut at every tile wrap (+47–92 % tris), or shrinking the bark into one non-repeating tile made it 4× blurrier. Square spray cells also squeezed tall sprays.

**Cause:** A tile inside an atlas can't repeat with plain UVs in both axes, and bark has to repeat up the trunk.

**Fix / rule:** Native layout, square 2048²: a vertical bark strip down one side (e.g. 512 px wide) and four 3:4 portrait spray cells (e.g. 768×1016) beside it. Import the texture with wrap **U Clamp, V Repeat**: bark UVs run U across the strip and V freely up the trunk, so any shader tiles it with plain UVs, one material, no extra seams. Cards take the cell's aspect (width = length × cell w/h), so generate sprays at 3:4 and they are never stretched.

Normal maps were dropped for these trees: on low-poly trees in VR, stereo exposes painted relief as fake.

**Verify:** bark texel density on the trunk matches the separate-material version; tri count unchanged from the two-material build; no visible seam where V wraps; spray aspect in the render matches the source image.
