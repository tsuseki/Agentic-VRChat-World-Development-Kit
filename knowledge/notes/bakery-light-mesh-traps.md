---
title: BakeryLightMesh traps: use one for explicit emitters, intensity is per-area, selfShadow off bakes black
topic: lighting-baking
tags: [Bakery, BakeryLightMesh, emission, intensity, selfShadow, samples2]
summary: Small or bright emitters need a BakeryLightMesh to light their surroundings (material emission alone is weak), its intensity is radiance per unit area so values never copy between emitters, and selfShadow=false with non-zero samples2 bakes black.
---
**Symptom:** "This emitter isn't working" — a visibly glowing screen/strip/lamp shade lights nothing around it, or raising intensity seems to do nothing.

**Cause / Fix / rule:**
1. **A visibly glowing emitter can contribute nothing useful without a `BakeryLightMesh`.** Bakery does export shared-material emission (`BakedEmissive` flag, `_EMISSION` keyword; see [bakery-bakes-material-emission-not-property-blocks](bakery-bakes-material-emission-not-property-blocks.md)), but small or bright emitters (screens, strips, bulbs) need an explicit `BakeryLightMesh` to light their surroundings. Diagnose by diffing components and material GI flags against a working emitter, not by tuning `_EmissionColor`.
   - Bakery hard-skips lightmapping any object carrying a `BakeryLightMesh` (a `continue` in `ftBuildGraphics.cs`). An object that must both emit and be lit needs splitting: a small emitter child holding the light mesh, and the visible body left lightmappable. `lightmapIndex == -1` on a light-mesh object is correct.
2. **`intensity` is radiance per unit AREA.** Output ≈ `worldArea × intensity`, and `worldArea` scales with `lossyScale` squared. Copying 0.30 from a 0.2008 m² shell to a 0.0154 m² bulb gave ~63× less power — the fixture lit nothing. Solve instead:
   ```
   newI = refArea * refIntensity * k / newArea
   ```
   Corollary: remeshing an emitter changes the bake; hold `worldArea × intensity` constant and the existing bake stays valid.
   "Intensity is a dead knob" almost always means **underpowered** — 3× of nearly nothing is still nearly nothing. Compare power against a working emitter before hunting mesh/UV/group failures.
3. **`selfShadow = false` with non-zero `samples2` bakes the emitter completely black**, with no warning. If you turn selfShadow off, zero `samples2`.

**Verify:** Pick the witness surface carefully — a surface that doesn't change across a huge intensity sweep may be occluded or bounce-only rather than proof of a dead emitter. Use rendered frame means.
