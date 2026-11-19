---
title: Lightmap vs Light Volume is a per-object test; low-poly trees with a clean UV2 stayed lightmapped
topic: lighting-baking
tags: [VRC Light Volumes, trees, lightmap, VRAM, voxel size, trunks, UV2, SoftCrown]
summary: Decide lightmap vs Light Volume for a complex static object by comparing look and VRAM; for 8 low-poly trees with a clean UV2 every volume layout cost about as much or more VRAM than their lightmap share and looked worse on trunks and crowns seen from above.
---
**Symptom:** Static trees with leaf cards look like good Light Volume candidates (complex UV2, many small cards), so a night garden of 8 low-poly olives was tested on Light Volumes against the shipped lightmap.

**Measured (8 trees, 50 room volumes already in the atlas):**

| Olive lighting | Extra VRAM |
|---|---|
| Lightmap share (garden atlas 4096 → 2944 at the same texel density when the trees leave it) | 8.1 MB |
| One box over all trees, 0.25 m | +17.7 MB |
| One box, 0.33 m | +8.8 MB |
| One box, 0.5 m | +3.9 MB |
| 4–24 boxes fitted to the trees, 0.25 m | +9.7 to +11.7 MB |
| 12 fitted boxes, 0.33 m | +4.5 MB |

**Look (same 6 poses, play mode, no capture light):** no layout matched the lightmap. Crowns lit by a volume read flatter from above (no darker crown interior); trunks lit by an uplight came out 20–70 % too bright; trunks at any voxel size (0.25 / 0.33 / 0.5 m) lost their shading because a trunk is about one voxel thick. Matching the lightmap on trunks would need ~0.1 m voxels (~250 MB). Light Volumes win only on cleanliness (no lightmap blotches on cards).

**Rule:** Decide per object type by a test, not by type alone: an object with a bad, fragmented UV2 can still be better on a Light Volume. Compare same-camera play-mode captures (look) and VRAM: the object's share of its lightmap (repack that lightmap at the same texel density with and without it) against the volume's atlas growth (voxels × 24 B, 3 RGBAHalf textures). Trunks and parts thinner than about 2 voxels lose their shading on any volume. Here the trees had a clean UV2, and a 0.25 m volume over even a small garden cost more than their lightmap share, so they stayed lightmapped.

**Verify:** Same-camera play-mode captures for both setups, and atlas bytes read from the generated Light Volume atlas, not estimated from box sizes (see `lv-atlas-packing-wastes-space-and-adds-noise`).

Related: [probe-light-small-objects-instead-of-lightmapping](probe-light-small-objects-instead-of-lightmapping.md), [lightmap-repack-tight-and-drop-empty-before-upload](lightmap-repack-tight-and-drop-empty-before-upload.md)
