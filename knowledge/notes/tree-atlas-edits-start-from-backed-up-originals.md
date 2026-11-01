---
title: Atlas-edit scripts rebuild from backed-up originals, keep the cell rects and match the shipped colour
topic: materials-textures-shaders
tags: [trees, leaf atlas, bark strip, texture edits, idempotence, colour grading]
summary: A script that edits an installed atlas applies its change twice when re-run on its own output (a bark squeeze doubled and striped the trunks with twig colour), so back up the originals once and always rebuild from them; when replacing a shipped atlas's cells keep the layout rects, grade new cells to the shipped leaf median and ship the new Atlas.json with it.
---
**Symptom:** After a second run of an atlas-edit script the trunks rendered striped yellow-green with the twig colour.

**Cause:** The generator read the already-installed atlas, so the bark-strip squeeze (made to fit a new twig column) was applied a second time.

**Fix / rule:**
- Back up the originals once (e.g. `tex_pre_<round>/`), keep the edit script beside them, and make the script read only from the backup. Reinstalling from the originals fixed the stripes.
- When replacing a shipped atlas's leaf cells, keep the layout's cell rects (e.g. `column_4cells`) and grade the new cells to the shipped leaf median (one beech atlas: HSV 0.243 / 0.671 / 0.549).
- The bark strip's u range can change with a rebuild (0.7734–0.9766 → 0.7617–0.9883), so the new `<Tex>_Atlas.json` ships with the atlas. Every bark column must stay at u ≥ 0.76: checkers that classify a packed face as bark by its u (`bare_limbs.py`) and the shader's `_BarkU0` rely on it.

**Verify:** diff the kept cells and bark strip against the original (pixel-identical where unchanged); re-run the script and check the output is byte-identical; a close-up of the thickest trunk.
