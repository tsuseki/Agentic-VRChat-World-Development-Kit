---
title: BakeryLightMesh traps: required for emissive bake, intensity is per-area, selfShadow off bakes black
topic: lighting-baking
tags: [Bakery, BakeryLightMesh, emission, intensity, selfShadow, samples2]
summary: Emissive materials add nothing to a Bakery bake without a BakeryLightMesh, its intensity is radiance per unit area so values never copy between emitters, and selfShadow=false with non-zero samples2 bakes black.
---
**Symptom:** "This emitter isn't working" — a visibly glowing screen/strip/lamp shade lights nothing around it, or raising intensity seems to do nothing.

**Cause / Fix / rule:**
1. **Bakery ignores Unity's `globalIlluminationFlags`.** A large `_EmissionColor` glows in the forward pass and contributes **zero** to the bake unless the object has a `BakeryLightMesh`. Diagnose by diffing components against a working emitter, not by tuning emission.
   - Bakery hard-skips lightmapping any object carrying a `BakeryLightMesh` (a `continue` in `ftBuildGraphics.cs`). An object that must both emit and be lit needs splitting: a small emitter child holding the light mesh, and the visible body left lightmappable. `lightmapIndex == -1` on a light-mesh object is correct.
2. **`intensity` is radiance per unit AREA.** Output ≈ `worldArea × intensity`, and `worldArea` scales with `lossyScale` squared. Copying 0.30 from a 0.2008 m² shell to a 0.0154 m² bulb gave ~63× less power — the fixture lit nothing. Solve instead:
   ```
   newI = refArea * refIntensity * k / newArea
   ```
   Corollary: remeshing an emitter changes the bake; hold `worldArea × intensity` constant and the existing bake stays valid.
   "Intensity is a dead knob" almost always means **underpowered** — 3× of nearly nothing is still nearly nothing. Compare power against a working emitter before hunting mesh/UV/group failures.
3. **`selfShadow = false` with non-zero `samples2` bakes the emitter completely black**, with no warning. If you turn selfShadow off, zero `samples2`.

**Verify:** Pick the witness surface carefully — a surface that doesn't change across a huge intensity sweep may be occluded or bounce-only rather than proof of a dead emitter. Use rendered frame means.
