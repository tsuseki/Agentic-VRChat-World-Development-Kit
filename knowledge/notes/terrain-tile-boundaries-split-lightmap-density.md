---
title: A build area straddling a terrain-tile boundary gets two lightmap densities
topic: lighting-baking
tags: [terrain, lightmap-density, bakery, uv2, lightmap-groups, seams]
summary: On large tiled terrain where only some tiles get dedicated lightmap atlases, anything straddling a tile boundary shows a straight tonal seam and blurred shadows on the low-density side; equal texels per metre on both sides makes the seam invisible.
---
**Symptom:** A dead-straight tonal seam runs through a build area exactly at a tile boundary; a vehicle just across it casts a blurred, chroma-fringed smear instead of a crisp contact shadow (under/clear luminance ratio 0.90 vs 0.42 on the other side).

**Cause:** Example: 100 tiles of 300 m. "Hero" tiles each get a private 4096 atlas = ~13.5 texels/m; the rest share one 4096 map between ~96 tiles, ~409 px each = ~1.4 texels/m.

**Promoting a tile takes two changes; the group alone does nothing.** The lightmap group sets atlas size, but density comes from how much of the atlas the tile's **uv2** covers. Tiles exported from one big terrain mesh each carry a 1/10 x 1/10 slice of a global unwrap, so a tile alone in a 4096 `OriginalUV` group still gets ~410 px = 1.36 texels/m and the bake looks "successful". Hero tiles need a generated copy of the mesh (identical verts/tris) with uv2 linearly stretched from its slice to ~0.004..0.996, assigned on the MeshFilter in the scene.

**Diagnose:** read `lightmapIndex` + `lightmapScaleOffset` per tile. Hero tiles show scale (1,1) on an index nobody else uses; shared tiles may also show `(1,1,0,0)` but share one index across ~100 renderers, so real density is `atlas / sqrt(N) / tileSize`. Don't read `(1,1,0,0)` as fine.

**Fixes, cheapest first:**
- Move the object fully onto the hero tile (needs a rebake; the old shadow stays burnt in).
- Promote the neighbour tile - costs a whole extra 4096 lightmap per tile (download/VRAM). Ask before spending it.
- Target **equal** texels/m on both sides, not "high enough": a matched-density boundary was invisible even top-down.
- Nothing changes until a rebake; keep any scripted group list and bake step in sync.

**When siting** anything that needs crisp ground shadows, check which tile it lands on first and keep build areas inside one hero tile.
