---
title: Weight terrain chunk lightmap scale by distance to the play area, measured from the chunk edge
topic: lighting-baking
tags: [terrain, scaleInLightmap, texel density, Bakery, lightmap budget]
summary: Within a group scaleInLightmap is a relative share of that group's atlas, so 4×/2×/1× weighting by distance to the route spends empty-desert texels on where players stand.
---
**When:** a huge terrain (e.g. 100 chunks of 300 m = 9 km²) where uniform density is either unaffordable or mush where players are.

**How:**
- Within one lightmap group, `m_ScaleInLightmap` is a **relative share of that group's atlas**, so weighting moves texels from empty land to the play area without adding VRAM.
- Grade each chunk by distance from the route/driving line to the chunk's **nearest edge**, not its centre (a 300 m chunk whose corner holds the hub has its centre 200 m away and would grade as empty).
- Result used: 16 core chunks at 4×, 16 mid at 2×, 68 outer at 1×.
- Give the 1–2 chunks under the main hub their own groups with dense, full 0–1 UV2 meshes.

**Verify:** per-renderer texels/m after the bake; see [tiled-terrain-low-texel-density-kills-contact-shadows](tiled-terrain-low-texel-density-kills-contact-shadows.md).
Related: [terrain-tile-boundaries-split-lightmap-density](terrain-tile-boundaries-split-lightmap-density.md).
