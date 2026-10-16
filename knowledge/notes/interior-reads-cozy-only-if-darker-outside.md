---
title: A cozy interior needs luminance contrast with the outside before it needs props
topic: lighting-baking
tags: [cozy, contrast, fog, ambient, exposure, interior]
summary: When the night outside measures brighter than the furniture inside, the room reads sterile; fix the contrast ordering with one uniform exposure pass before adding props.
---
**Symptom:** a cabin interior reads sterile/bare. Measured sRGB luminance: ceiling 0.58, night fog outside the windows 0.45, far wall 0.47, beds 0.37 — the whole frame in a 0.21-wide band, outside brighter than the furniture.

**Cause:** not a props problem. Contributors, in order: pale daylight-like fog colour; a tri-light ambient flooding every surface from all directions so ceiling and floor matched; ceiling light strips making the ceiling the brightest large surface. Also only one material family in the room.

**Fix / rule:**
- Measure region luminance from a render first. If the exterior out-measures the interior, that ordering *is* the bug; adding cushions to flat lighting only adds more beige lumps.
- Darken the exterior as a **uniform-exposure** pass: fog colour, skybox ground/horizon/zenith colours, any shader uniforms synced to fog, the baked sky light, the baked sun, vegetation emission and impostor grading all scale by the **same factor**, or the locked brightness ordering (e.g. trees < ground < fog < horizon glow) breaks. Do it atomically and verify with a bake.
- Afterwards re-check objects that relied on ambient (see [global-dim-pass-breaks-ambient-only-objects](global-dim-pass-breaks-ambient-only-objects.md)).
- Prop pack FBXs often ship with **Generate Lightmap UVs off**; enable and reimport before making them lightmap-static.
- For a lived-in look, a slept-in bed (rumpled duvet, soft creased pillows, e.g. cloth-sim folds) reads cozier than made beds with box pillows.
