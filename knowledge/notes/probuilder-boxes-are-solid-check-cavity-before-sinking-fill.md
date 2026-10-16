---
title: Scripted ProBuilder planters are solid boxes: soil fill must sit proud
topic: geometry-meshes-uvs
tags: [ProBuilder, planter, pot, soil, cavity, occlusion, texture tiling]
summary: Scripted ProBuilder pots are closed-top solid boxes with no cavity, so sinking soil below the rim hides it completely; check for a cavity before moving fill.
---
**Symptom:** Soil discs sitting 17-60 mm above their pot rims read as lids, so they were sunk to 25 mm below the rim, and all of them vanished.

**Cause:** Every planter was a ProBuilder box: **24 vertices, top face present at the centre**, a solid block rather than a tub. There is no cavity; the top face occludes anything below it.

**Fix / rule:**
- Check for a cavity before moving fill: vertex count (24 = plain closed box) plus a point sample of whether a face exists at `(centre.x, bounds.max.y, centre.z)`.
- For a solid box, leave the disc **proud** and make it legible by re-tiling its albedo per renderer so the grain reads at each pot's real size (`_MainTex_ST` scaled from the pot's own bounds). One shared soil material otherwise gives a 3 m grain on a 0.3 m pot.

**Pitfalls:**
- A "proud vs sunk" audit must compare each soil top against **its own container's** rim; a global threshold passes everything.
- Name matching gives false positives (a "pot" substring matched spotlight names). Match on geometry and material, not names.
