---
title: Sparse variety cells are several small real branchlets at the full cells' leaf size, never one branch shrunk by card scale
topic: materials-textures-shaders
tags: [trees, leaf atlas, spray variety, shoot cell, sprig cell, card scale, opacity, leaf size]
summary: Build a sparse shoot or sprig atlas cell from 5–7 (shoot) or 3–4 (sprig) small branchlets cut from the family's own sprays at the full cells' leaf pixel size (card scale ≈ 1), matched by opaque share against the full cells (shoot 50–60 %, sprig 30–40 %), never from one branch drawn bigger and shrunk by Cards.json `scale`, never from drawn stems; a cell redrawn at a new leaf size needs a tree rebuild, not a UV-only swap.
---
**Symptom:**
- A variety cell drawn as ONE shoot or sprig at card scale 0.59–0.96 (olive leaf 113 px against 65 px in the full cells) was rejected: "you could've made more smaller branches in that space".
- A cell built from bark-strip "stems" carrying small leaf pieces read as poles and was 80 % empty.
- After a redrawn cell was swapped in by UV only, its leaves rendered 0.59× too small.

**Cause:**
- One big branch shrunk by `scale` carries few large-pixel leaves and reads as a single twig, not a sparse spray.
- Drawn stems have no real twig structure.
- Card length was built as tuft px × `scale`: old cards at 0.591 render a new scale-1 cell 0.59× too small.

**Fix / rule:**
- Compose each variety cell from small real branchlets cut out of the family's own sprays (`scripts/compose_cells.py`, see the branchlet-cut note), at the full cells' leaf px (card scale ≈ 1, within ±10 %). Every texel comes from a real spray: cut subtrees plus the source spray's own trunk and limb starts as the base.
- Opacity targets win over leaf counts. Measure the alpha > 0.45 share of the cell against the full cells:
  - shoot cell: 5–7 branchlets, each about 1/3 of the cell height, radiating from a short natural base, at 50–60 % of the full cells' opacity (10–16 leaves per branchlet were needed; 6–12 only reached about 45 %);
  - sprig cell: 3–4 sprigs in the lower 2/3 at 30–40 % (12–14 leaves each; 4–8 only reached about 20 %).
- A piece may repeat across cells but never nests or repeats within one cell.
- Keep the kept cells and the bark strip pixel-identical and the atlas size unchanged.
- A redrawn cell that changes leaf px needs a tree rebuild. A UV-only cell swap is valid only between cells at the same scale.
- Automatic leaf length works for broad single leaves: the median PCA major axis of single foliage components (150–4000 px, major/minor ≥ 2.2) agreed within 2 % across olive cells (63.7 / 64.4 / 65.2 / 65.2 px). For needle tufts every automatic metric (ray length, inscribed radius, needle width) was unreliable: set the tuft px by hand.

**Verify:** per composed cell `OPAQUE … x ref cells` and `LEAFPX` from `compose_cells.py`; key-spill 0 on mips ≥ 1; after the rebuild, crown sky, `bare_limbs.py` and tris against the shipped build; a before / after close-up of varied cards.
