---
title: Cut real branchlets out of a spray image by treating its alpha mask as a tree; needle tufts need their own ownership model
topic: materials-textures-shaders
tags: [trees, leaf atlas, spray variety, image processing, geodesic distance, needle tufts, skeleton]
summary: Erasing a small disk at a twig texel disconnects the part of the spray beyond it, a real branchlet with its own twig; survey cut points on a grid, paste pieces rotated and scaled about the cut onto a base made from the source trunk, and snap each piece to a base limb end; overlapping needle tufts form one blob, so pines need tuft centres, needle ownership and cheapest root paths instead.
---
**Symptom:** Composing variety cells needed branchlets that look drawn by the same hand as the full cells; drawn stems were rejected. On pine sprays the mask cut found 0 candidates even with relaxed limits. On a green-stemmed maple the stem fell apart, and one cell turned fully opaque.

**Cause:**
- Broadleaf sprays: the alpha mask is a tree, so topology gives clean pieces.
- Needle sprays: overlapping tufts make one opaque blob, and a cut leaks the whole spray.
- A colour mask `G > R + 4` (foliage) holds on 45–75 % of green-tinted stem texels, so `mask & ~foliage` cuts the stem apart. When the root texel itself is masked out, `lab[root] == 0` selects the background.

**Fix / rule** (`scripts/compose_cells.py`):
- Treat the alpha > 100 mask as a tree rooted at the stem's bottom texel, with geodesic distance from `skimage.graph.MCP_Geometric`.
- Erase a disk of radius ≈ twig half-width + 1.5 at a twig texel: the part beyond it is a branchlet with its own twig.
- Survey thin twig texels on a 6 px grid; keep pieces with 3–20 leaves and 120–450 px extent.
- Paste each piece rotated and scaled about its cut point, premultiplied alpha. Draw the base (the source trunk within geodesic `keep_d` of the root) over the pieces.
- In the spec, put each piece's `at` on a base limb end: a skeleton endpoint of the base mask at geodesic ≥ 0.9 × keep_d. Anywhere else the piece floats.
- Needle mode (`"mode": "needle"`, `survey --needle`):
  - tuft centres by a Hough vote along the structure-tensor needle direction (4–70 px), peaks of `maximum_filter(41)` above 0.15 × max;
  - each needle texel belongs to the tuft whose centre is within 26 px, or that it is radially aligned with (cos ≥ 0.85) within 78 px;
  - the twig tree is the cheapest path from the root to each tuft (bark cost 1, other opaque texels 6); a cut takes only the tufts whose path passes it;
  - masks: bark = R > G + 12 at alpha > 100; foliage = G > R + 4 at alpha > 128.
- Needle-mode gotchas:
  - a sibling tuft centred on the cut gets pulled in → exclude tufts within 1.2 × Rin of the cut;
  - other tufts' needles near the cut leak in → clear non-owned foliage within 1.5 × Rin;
  - detached fragments float → keep only parts that touch the twig;
  - the twig stops short of the cut and the piece floats off the base → keep twig texels inside the cut disk;
  - leftover base limb stubs show → `scripts/trim_stubs.py`.
- Green stems: fall back to the label of the nearest non-empty texel (`distance_transform_edt(lab == 0, return_indices=True)`); base `leaf_mask: "wide"` excludes only leaf bodies (`dilate(open(lf, 3), 2) & lf`); `leaf_mask: "none"` excludes nothing and needs a short `keep_d`.

**Verify:** read the survey's `candidates_<cell>.png` before writing the spec; the composed cell over grey; `OPAQUE` against the reference cells; no piece floating off the base.
