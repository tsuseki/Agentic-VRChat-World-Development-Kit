---
title: Find the stored shots a model change affects by toggling its renderers
topic: agent-workflow-verification
tags: [re-shoot, cameras, forceRenderingOff, promo stills, diff mask]
summary: To decide which stored camera shots need a re-shoot after an asset change, render every camera small with the asset's renderers forceRenderingOff on vs off and threshold the changed-pixel share, inspecting the mask for animated-water and glitter false positives.
---

**Symptom.** After a hero model changed, the choice was re-rendering every stored still (slow) or eyeballing which ones showed it (misses background appearances).

**Cause.** An asset often appears small, behind other objects or in reflections in shots nobody associates with it.

**Fix / rule.** Render every stored camera at low resolution twice: the asset's renderers with `forceRenderingOff = true` and false. Threshold the share of changed pixels per camera and inspect each mask: animated water, sun glitter and wind give false positives, so freeze them or mask them out.

**Verify.** On 19 day and 3 dusk cameras the method picked exactly 7 for re-shoot; the masks showed the asset in each. Positive control: a camera framed on the asset must trip.
