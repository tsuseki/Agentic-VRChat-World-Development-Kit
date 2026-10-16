---
title: Near-white albedo on large interior surfaces makes sealed rooms bake hypersensitive and blown
topic: lighting-baking
tags: [albedo, GI, multi-bounce, ceiling, blown highlights, Bakery]
summary: Multi-bounce gain is ~1/(1−albedo), so an albedo-1.0 ceiling turned an 18% light increase into a 5× brighter bake; lower the albedo of the big bright surface, not the lights or the floor.
---
**Symptom:** adding a few lights to a sealed hall (+18 % flux) made the bake ~5× brighter; blown pixels went 2.7 % → 11.8 %. Dimming lights only trades "too bright" for "too dark". Overbright near-white ceilings can also show denoiser blotches that look like clouds through a hole.

**Cause:** in a sealed room multi-bounce gain is roughly `1 / (1 − ρ)`. An untextured ceiling with albedo (1,1,1) makes the enclosure hypersensitive to any added light and guarantees white surfaces clip.

**Fix / rule:**
- Treat albedo 1.0 on any large interior surface as a bug; no real surface has it. Ceiling 1.0 → 0.75 took blown 10.2 % → 0.51 % with dark% unchanged.
- **Audit by lit surface area across the whole area**, not material by material: sum per-submesh world triangle area per material, sort by m², flag `max(rgb) > 0.85 && _MainTex == null`. A second offender (0.97/0.95/0.90, untextured, 719 m²) was found this way after the first fix. Textured materials with a white tint are usually fine.
- Darken the surface driving the gain (ceilings, large bright faces). Don't fix over-brightness by darkening the **floor** — that leaves a dark, unreadable floor once the real culprit is fixed.
- Invisible `ShadowsOnly` occluder boxes default to `Default-Material` (pure white) and still bounce light in the bake — see [shadowsonly-occluders-default-to-white-and-bounce-light](shadowsonly-occluders-default-to-white-and-bounce-light.md).

**Pitfalls:** rebaking reflection probes from the overbright state made the room *brighter* (probes capture current lighting and feed it back as ambient specular). Rebake probes **last**, after lightmaps are final.
