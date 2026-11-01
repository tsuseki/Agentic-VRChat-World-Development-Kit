---
title: A pale halo around leaves can be the image viewer's downscale, not the render
topic: agent-workflow-verification
tags: [foliage, halo, alpha cutout, image viewer, resampling, verification]
summary: A foliage capture viewed downscaled showed a pale net around every leaflet that did not exist at native resolution; inspect 1:1 and nearest-neighbour crops and a magenta-sky render before blaming crunch, alpha-to-coverage, cutoff or mips.
---

**Symptom.** A 1600×900 foliage capture, viewed fitted to about 1176 px wide, showed a pale net around every leaflet. It looked like a cutout halo (bright RGB bleeding from under alpha 0).

**Cause.** The viewer's downscale blended the dark leaf edges with the bright sky behind them. At 1:1 and in 4× nearest-neighbour crops the edges were dark and crisp, and a box-filter downscale showed no halo.

**Fix / rule.** Before changing textures or shader settings for a "halo", check the pixels at native resolution (1:1 and 4× nearest-neighbour crops) and render the same camera with the skybox replaced by solid magenta, then count pale edge pixels per variant.

**Verify.** Controls on the same camera: pale-pixel count 1472 baseline, 1443 with the original atlas, 1484 with alpha-to-coverage off, 1480 with mip bias 0: no variant moved it, and the atlas was byte-identical to the original with RGB already dilated under alpha 0. Nothing to fix.

**Related.** `metrics-that-cannot-see-their-defect.md`.
