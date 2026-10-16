---
title: Hit a target luminance and hue in two renders by solving a linear model
topic: probes-reflection-and-light
tags: [lighting-tuning, emission, materialpropertyblock, spherical-harmonics, linear-solve, render-metrics]
summary: When a knob enters shading linearly, measure the zero-input render and solve C = Z + m*D per channel to land a target luminance and hue on the first attempt instead of trial and error.
---
**When:** You need a runtime-lit renderer to land at luminance L and hue r/b, and the knob is linear in the shading - a property-block `_EmissionColor`, a `CustomProvided` SH block, a `_Color` tint. Trial-and-error usually converges on level while leaving hue wrong.

**How:** per channel, `C = Z + m*D`:
- `Z` = render with the knob forced to **zero** - everything you don't control (fog, reflection-probe specular, a second light path). Measure it, never assume zero; on a metallic trim it was 20-22% of the total.
- `D = C_current - Z` = the part the knob drives.
- `m_ch` = per-channel multiplier on the current knob value.

One luminance and one hue target across three channels needs a third constraint; a geometric split behaves well:
```
q      = sqrt(rb_target / rb_current)
gain_r = G*q ,  gain_g = G ,  gain_b = G/q      # G solves the luminance target
m_ch   = (gain_ch*C_ch - Z_ch) / D_ch
```
Then factor `m` into the component's knobs, e.g. a scalar (anchor on green) times a tint `(m_r/m_g, 1, m_b/m_g)`.

**Pitfalls:**
- Isolate the object's pixels by renderer-ownership toggle (render, render with `renderer.enabled = false`, take changed pixels), not a rectangle or colour mask. The second frame also gives the abutting surface's value.
- Gamma hop: `SetColor` converts gamma->linear, `SetVector` doesn't. Solve in linear, convert back with `1.055*x^(1/2.4) - 0.055`, then divide out any scalar the component multiplies in.
- A texture mask in the path tints as well as attenuates (an emission map biased rendered r/b 1.30x warm). Measure the rendered hue, not the typed one.

**Verify:** predicted L 0.02112 / r/b 0.450 -> measured 0.02111 / 0.451 on the first attempt. If the first re-render misses, the knob isn't linear - find the missing path (second light, keyword, stale shader program) instead of iterating.
