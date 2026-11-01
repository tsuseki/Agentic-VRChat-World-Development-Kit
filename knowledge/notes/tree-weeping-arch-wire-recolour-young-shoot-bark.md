---
title: Bare weeping arch tops that read as wire are recoloured as young-shoot bark per face, not covered with cards
topic: materials-textures-shaders
tags: [trees, weeping willow, strand atlas, bark columns, twig colour, bare limbs, crest cards]
summary: On a weeping strand atlas every card hangs from under its limb, so the limb axis is always the curtain's top edge and no crest card covers it; colouring the arch bark faces in the species' young-shoot colour (per face, by girth plus a top height band) removed the dark wire hoops at 0 tris, and mapping each BARE_END back to the built skeleton showed the real cause of bare tips.
---
**Symptom:** Bare arch tops of a weeping crown read as dark wire hoops against the sky from 16 m. `bare_limbs.py` reported a few `minor` bare ends near the arch tips.

**Cause:**
- On a strand atlas (attach at the cell's bottom edge, cards hang), every card's attach point sits under the limb, so the limb axis is always the curtain's top edge.
- Merged limbs fuse the thin arcs into thick tubes, so a per-tube "is it a twig" test misses the arch tops.
- The tip card sits at 0.97 of the tip member by default, leaving the last 3 % bare: about 0.3 m on a 9–12 m arch.

**Fix / rule:**
- Crest cards don't fix it on strand atlases. Six variants failed: follow, short level, lifted 0.25 m (floating under `bare_limbs`), finer tips, fan cells, finer grid.
- Recolour instead: a twig bark column in the atlas in the species' young-shoot colour (yellow-green for willow), assigned per face to every ring under a girth (0.45 m) AND to every face above a height band (0.72 × tree height). Girth alone left the thicker upper scaffolds grey against the sky; the height band fixed it (twig faces 552 → 592 of 720).
- Root the tip card at the very end: `low_tips` `tip_t` 0.995 (minor bare ends 5 → 0 and 1 → 0). Crown-level `tip_t` is a separate key for the card on every terminal end.

**Verify:** top views of the crown against the reviewer's frames, plus `bare_limbs.py`.

**Pitfalls:**
- Find the cause of a bare end by mapping the `BARE_END` coordinate back to the built skeleton: `bare_limbs.py` prints packed Blender coordinates, so divide by the pack scale (e.g. 0.7) for built ones, then dump the branches whose ends lie there (depth, length, terminal, cards on them). Here the bare ends were arch tips carrying 24–44 cards, so neither `low_tips` `min` nor ground or clear-volume rejection was the cause.
- Changing a shared atlas's bark columns means re-packing every variant on that atlas, including untouched ones.
