---
title: Tiled terrain at ~1 texel/m casts no readable shadows and shows a seam at every tile
topic: lighting-baking
tags: [terrain, texel density, seams, fixSeams, contact shadow, lightmap]
summary: At ~1 texel/metre nothing throws a ground shadow and props read pasted on; separate tile renderers are independent charts, so each boundary shows a bright bleed line that fixSeams cannot stitch.
---
**Symptom:** several independent reviews of different sites report "props don't sit on the ground" and "hard tonal step through the site". A 4.4 m object under a 43° sun should throw a ~5 m shadow and throws none. Top-down the map looks like a quilt.

**Cause:** one map-wide property, not local defects:
- Terrain tiles baked at ~0.94–0.99 m/texel. At that density no contact shadow reads.
- Bakery `fixSeams` stitches charts **within one mesh**; 100 separate tile renderers are 100 independent charts. Every boundary shows a ~1-texel bright bleed line (edge texel sees unoccluded sky) plus a per-tile tone step.
- Sites placed on round coordinates sit exactly on tile boundaries when the tile pitch is round too.

**Fix / rule:**
- Check atlas headroom first: here the tiles used ~2.06M of a 4096² atlas's 16.7M texels, so density could double for free. Doubling narrows the seam band and sharpens contact shadows but does not remove the discontinuity.
- A real fix is merging terrain into fewer meshes or authoring UV padding/bleed — both cost lightmap memory.
- Cheap mitigation: nudge important sites 8–15 m off the tile grid.

**Verify:** orthographic top-down render over ~1400 m: tone steps with bright boundary lines = lightmap. One shared material instance across all tiles rules out the shader. Per-tile mean luminance from the atlas alone is not conclusive (tiles differ in content). Before treating a bedding/contact-shadow complaint as a prop problem, check terrain texel density at that spot.
Related: [terrain-tile-boundaries-split-lightmap-density](terrain-tile-boundaries-split-lightmap-density.md) (hero tiles need their own full-range UV2, not just their own group).
