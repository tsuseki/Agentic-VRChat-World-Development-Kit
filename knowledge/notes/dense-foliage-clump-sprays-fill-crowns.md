---
title: Dense foliage-clump sprays fill a card crown without any mesh change; avoid smooth oval clumps
topic: materials-textures-shaders
tags: [trees, foliage, leaf atlas, image generation, prompt, sprays, crown fullness]
summary: Replacing sparse leaf sprays with dense, ragged foliage clumps (cell coverage 0.23–0.37 → 0.46–0.65) moved olive crowns from 0.41 to 0.20–0.28 sky with the same mesh; smooth oval clumps read as flat solid blobs.
---
**Symptom:** Card crowns stayed see-through after adding cards; sky fraction inside the crown was ~0.41 on olives.

**Cause:** The generated sprays were sparse twigs with few leaves: only 0.23–0.37 of each atlas cell was leaf, so every card was mostly transparent.

**Fix / rule:** Regenerate the sprays as dense clumps. Prompt wording that worked: "ONE dense, full clump of foliage filling the frame, many overlapping small leaves, no gaps inside the clump, the outline ragged and tufted" (keep the real leaf-size and leaves-only wording). Cell coverage rose to 0.46–0.65 and the olives dropped to 0.20–0.28 sky with no change to the mesh or config.

**Pitfall:** smooth, oval clumps read as flat solid blobs once on the tree (two species had to be regenerated). Insist on a ragged, tufted outline.

**Verify:** per-cell alpha coverage of the atlas (opaque texels / cell area) before building, then the eye-level sky fraction ([full-crowns-measure-sky-fraction-inside-crown](full-crowns-measure-sky-fraction-inside-crown.md)) and an eye-height render checking the outline isn't blobby.
