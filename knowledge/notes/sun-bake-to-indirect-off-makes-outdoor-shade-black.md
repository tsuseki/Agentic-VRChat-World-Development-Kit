---
title: Outdoor shade bakes pitch black when the sun has bakeToIndirect off
topic: lighting-baking
tags: [Bakery, BakeryDirectLight, bakeToIndirect, shade, outdoor, GI]
summary: With bakeToIndirect=false the sun produces zero bounce; with black flat ambient every shaded exterior bakes to ~0 with a hard edge.
---
**Symptom:** every shaded exterior (porches, arcades, alley grass) bakes pure black with a hard shadow edge, while sunlit ground is bright.

**Cause:** the `BakeryDirectLight` had `bakeToIndirect = false`; Bakery builds its indirect pass list only from lights with that flag, so sunlight produced no bounce. With `ambientMode = Flat` and ambient black, nothing else filled shade.

**Fix / rule:** sun `bakeToIndirect = true`, `indirectIntensity = 1.0`; sky light samples 32 → 64 if it is the other indirect contributor. Adds no artificial lights. If the scene overshoots, lower the sun's `indirectIntensity` below 1 rather than dimming the sun.

**Diagnostic order that worked:** rule out light-linking (all group and light `bitmask` values = 1), then ShadowsOnly occluders (there were none), then the sun's own indirect flag.
