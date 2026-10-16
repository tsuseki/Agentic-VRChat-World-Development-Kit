---
title: Pieces cut from a photoscan are hollow shells that fool bounding-box tests
topic: geometry-meshes-uvs
tags: [photoscan, shell, thickness, bounding-box, volume, quality-gate]
summary: Fragments cut from a photoscan surface are open shells with no thickness, and a curled shell has a chunky bounding box, so gate them on volume divided by surface area, not bbox aspect.
---
**Symptom:** Rock chips or debris harvested from a photoscan render as torn cardboard - razor-thin silhouettes, visible black backfaces, often standing on edge - while an automated flatness gate passes them.

**Cause:** Photoscan assets are surfaces, not solids. A *curled* shell has a near-cubic bbox: chips scored 0.76-0.98 on thin/long ("chunky, passes") while their equivalent slab thickness (volume / surface area) was 1.1-9.2 cm (one was 1.1 cm across a ~1 m envelope). Bbox fill ratio said the same: 0.017-0.178, where a solid pebble is 0.3-0.5.

**Fix / rule:**
- Gate harvested photoscan pieces on **volume / surface area** (or bbox fill ratio), never bbox aspect.
- Fix by shell-thickening to >= 8-12 cm with capped boundaries, or swap in closed proxy meshes.
- Re-seat broadest-face-down afterwards - a solidified piece has a different resting face.
