---
title: A lamp can still read as switched on because of its albedo, not emission
topic: probes-reflection-and-light
tags: [albedo, lamp shade, switched off, MaterialPropertyBlock, SetPropertyBlock, night state]
summary: A fixture whose albedo was authored to be seen under its own bulb still reads as lit after emission is killed; judge against the key light and fix with a _Color block.
---
**Symptom:** In a lights-out state, table-lamp shades with no emission at all still read unmistakably as "on": the brightest, warmest thing in a blue room.

**Cause:** The shade albedo is an ivory (0.640, 0.592, 0.534) meant to be seen under a warm bulb. Measured luminance 0.0438 against a 0.0334 window sky, warm (r/b 0.775). There is no emission to remove.

**Fix / rule:** Apply a `_Color` property block for the alternate state, pushed down and toward neutral: (0.30, 0.31, 0.33) x 1.20 gave luminance 0.0192, r/b 0.47, 0.55x the window sky. No rebake.
- Judge a surface against the **key light** (window/sky), not its neighbours. "Darker than the wall next to it" would have passed.
- After darkening something, re-check what is beneath it: at a stronger scale the lamp plinth became brighter than the shade.
- Keep albedo and emission passes as **disjoint lists**: `SetPropertyBlock` replaces rather than merges, so a renderer in both keeps only the last one applied.
