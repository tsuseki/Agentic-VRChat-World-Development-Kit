---
title: Seasonal tree states are one extra atlas per season on the same cards, shipped as a material swap
topic: materials-textures-shaders
tags: [trees, seasons, autumn, winter, blossom, leaf atlas, image edit, material variants]
summary: Bloom, summer, autumn and winter versions of a card tree share one mesh; each season is an atlas with identical cell rects, attach points and bark strip, generated as image edits of the previous season's approved cells (autumn as a per-leaf recolour of summer with identical alpha), and a bare winter tree is a bare-twig atlas on the same cards, never a bark-only mesh.
---
**Symptom:**
- A bark-only winter mesh (cards removed) read as a dead skeleton of a few thick limbs.
- Leafy sprays generated as edits of blossom sprays came out spring-lime with leaves too big.

**Cause:** Without cards only the scaffold limbs remain; a real bare crown is a mass of fine twigs. Image edits drift in leaf size and hue from the reference cells.

**Fix / rule:**
- One mesh, one atlas per season, shipped as a material swap plus prefab variants; the main season is the default prefab.
- Generate each season's sprays as image edits of the previous season's APPROVED cells: summer from the raw bloom generations, winter from the approved summer picks. Autumn is a per-leaf recolour of summer, alpha identical.
- `branch_atlas.py` pins the stem base to the cell bottom-centre, so the new atlas comes out with identical cell rects and attach points. Reuse the shipped `<Tex>_Bark_Albedo.png`, so the bark strip is pixel-identical.
- Ask for smaller leaves in a second edit prompt, then grade to the species (blossom → summer needed hue +9°, s × 0.88, v × 0.90, to about 95° / 0.71 / 0.52).
- Winter = a bare-twig atlas on the same cards, pruned until the crown reads bare (see the twig-pruning note); it may keep winter buds.
- Blossom trees work by the same method: open twig sprays carrying blossom clusters, keyed on a colour far from the petals (cyan for pink).

**Verify:** per season: rects, attach points and bark strip identical to the base atlas; the key colour 0 on every mip (`check_key_spill.py --key <key>`); crown sky and `bare_limbs.py` with the season's atlas swapped onto the shipped mesh; every season atlas approved as a PNG before install.

**Calibration** (`crown_fullness.py`, one cherry family):

| State | Opaque per cell | Crown sky |
|---|---|---|
| bloom | 0.28–0.31 | 0.15–0.18 |
| summer leaves | 0.21–0.23 | 0.17–0.22 |
| winter twigs, unpruned | 0.07–0.09 | 0.34–0.40 (read as brown leaves) |
| winter twigs, pruned | 0.013–0.029 | 0.62–0.65 (reads bare) |
