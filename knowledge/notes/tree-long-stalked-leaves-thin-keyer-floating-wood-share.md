---
title: Long-stalked leaf sprays need a keyer without opening or erosion; pick sprays by floating-leaf share and wood share
topic: materials-textures-shaders
tags: [trees, leaf atlas, chroma key, leaf stalks, floating leaves, wood share, twig colour, spray selection]
summary: Opening plus 1 px erosion in the leaf keyer deletes the 1–3 px stalks of birch and maple leaves, leaving 25–60 % of opaque texels as leaves floating off the twigs; key those sprays with a soft ramp and no morphology, score candidates by floating share (≤ ~4–6 % per cell) and wood share (broadleaf ≤ 0.18, needles ≤ 0.08), and cut wood by re-picking lower-wood sources, not by image processing.
---
**Symptom:**
- Birch and maple atlases showed leaves hanging in the air beside their twigs: after the cell fit 25–60 % of opaque texels were pieces more than 8 px from any twig (short-stalked oak sprays: 0 %).
- A shipped beech atlas measured 36 / 24 / 18 / 17 % floating per cell.
- A birch atlas showed too much twig from outside (wood share 0.20–0.32 per cell).
- Near-white silver twigs read as pale lines through the crown from outside.

**Cause:**
- `process_gpt_textures.leaf()` opens the matte and erodes it by 1 px, which removes the 1–3 px stalks that connect each leaf to its twig.
- Generated sprays differ a lot in how much bare twig they draw; image processing can't remove wood without cutting the twigs that carry the leaves.

**Fix / rule:**
- Key long-stalked sprays with `scripts/thin_key.py` (soft ramp, no opening, no erosion; solid pieces under 60 px dropped, ramp kept within 2 px of solid texels, every non-solid texel recoloured from the nearest solid one).
- Floating share = opaque pieces more than 8 px from the stem network / opaque texels. Score candidate sprays with it (`scripts/spray_metrics.py sprays … [--thin]`) and pick the lowest; target ≤ about 4–6 % per full cell. Re-picking the beech sources this way gave 0.4 / 4.8 / 6.1 / 9.4 %; candidate scores ranged 0.004–0.286.
- Wood share = opaque texels in the top 80 % of a cell that are not foliage-coloured (hue outside 55–180° or saturation ≤ 0.2) / opaque texels. Targets: broadleaf ≤ 0.18 per cell, needle sprays ≤ 0.08. Shipped references: oak 0.11–0.15, beech 0.07–0.13, rosemary 0.11–0.16, sugar maple 0.07–0.15; old flat-lay spruce 0.17–0.21. Show both numbers on every atlas review sheet.
- Cut wood by re-picking lower-wood source sprays. Birch, wood / floating per cell: full stalk thickening 0.32 / 0.22 / 0.29 / 0.20 with 0–3.6 % floating; stalk-only thickening plus tip trimming 0.12–0.22 wood but floating up to 27 %; a source swap (stalk-only thickening, no trim) 0.12 / 0.16 / 0.18 / 0.08 with 3.4–14 % floating, accepted as reading much more like a real birch. Thicken only the leaf stalks plus a 1 px grey closing of twig gaps; never trim bare twig tips on thin broken twigs (the trim can't reach leaves through the gaps, cuts twigs off, and floating rises).
- Twig colour: twigs match the bark, and pale fails as well as red. Darken near-white or silver twigs to a mid grey-brown (value about 0.35–0.45, darker than a smooth grey trunk) in every season's atlas, alpha unchanged (beech: non-foliage texels to hue 30°, saturation 0.22, median value 0.71 → 0.40).

**Verify:** `spray_metrics.py atlas <atlas> <Cards.json>` per cell, the atlas over grey, and a crown close-up from outside at 3–10 m.

**Related:** re-cutting a sprig cell from the same spray at other seeds gave little (floating 11.8 / 11.3 / 8.1 %, wood 0.081–0.095): change the source instead.
