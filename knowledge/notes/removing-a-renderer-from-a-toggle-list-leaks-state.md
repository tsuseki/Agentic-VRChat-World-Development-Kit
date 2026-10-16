---
title: Removing a renderer from a runtime toggle list leaks its ON state
topic: udonsharp-networking
tags: [state-toggle, materialpropertyblock, lightProbeUsage, serialization, lighting-states, runtime-switch]
summary: In a symmetric ON/OFF toggle over a renderer list, dropping a renderer from the list leaves its stale property block and any serialized renderer fields the ON path set, because the OFF path no longer visits it.
---
**Symptom:** After moving a renderer out of a day/night (or variant) toggle array, it renders unchanged by its new setup, or the shipped default state differs from its siblings.

**Cause:** "ON sets X on everything in L; OFF resets X on everything in L" is only symmetric while L is fixed. Two leaks:
1. **Stale `MaterialPropertyBlock`.** SH coefficients (`unity_SHAr/Ag/Ab`) set via a block are read by the shader unconditionally (not gated on `lightProbeUsage`), so a renderer newly bound to a real lightmap kept rendering its old synthetic SH and measured identical.
2. **Serialized renderer fields.** `lightProbeUsage` stayed stuck on `CustomProvided` in the OFF/shipped state. Property blocks are runtime-only and evaporate; renderer fields serialize and ship.

**Fix / rule:**
- Don't just remove an entry - **migrate** it to a list whose ON path gives it a clean block and whose OFF path calls `SetPropertyBlock(null)`. Reproduce once by hand what the OFF path used to do for it.
- Add a **shipped-state assertion over the whole scene**, not over the list: e.g. `count(lightProbeUsage == CustomProvided) == 0` and no property blocks present, so the next removal fails loudly.
- The shipped/default state is the one nobody screenshots; deviations there survive every review of the feature.

Related: [setpropertyblock-replaces-not-merges](setpropertyblock-replaces-not-merges.md)
